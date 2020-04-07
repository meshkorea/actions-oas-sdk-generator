#!/usr/bin/python3
import sys
import subprocess
import json
import yaml
import re
import os

github_token = os.getenv("INPUT_GITHUB_TOKEN")
github_repository = os.getenv("GITHUB_REPOSITORY")
print(os.environ)
github_owner = github_repository.split("/")[0]
npm_repository = f"https://npm.pkg.github.com"
npm_name = f"@{github_repository}"

reponame = github_repository.split("/")[1]
service_name = reponame.replace("vroong-", "")

spec_loc = os.getenv("INPUT_SPEC_LOCATION")
generator = os.getenv("INPUT_GENERATOR")


def parse_version(location):
    with open(location) as f:
        if re.match(".*\\.json", location):
            spec = json.load(f)
        else:
            spec = yaml.load(f)
        return spec["info"]["version"]


version = parse_version(spec_loc) + "-build" + os.getenv("GITHUB_RUN_NUMBER")

script_loc, *args = sys.argv
extra_parameter = {}
for arg in args:
    if not arg.startswith("--"):
        continue
    match = re.search("^--(.+)=(.+)$", arg)
    if not match:
        continue
    key, val = match.groups()
    if key in ["api-package", "model-package", "model-name-prefix", "model-name-suffix"]:
        extra_parameter[key.replace("-", "_")] = val


def run_generator(service_name, spec_loc, generator, library, **kwargs):
    params = ["-g", generator]
    if library:
        params.extend(["--library", library])

    for key, val in kwargs.items():
        params.append("--" + key.replace("_", "-"))
        params.append(val)

    subprocess.check_call([
        "java", "-jar", "/openapi-generator/openapi-generator-cli.jar", "generate",
        "-i", spec_loc, "-o", ("/openapi-generator/" + service_name), *params
    ], stdout=sys.stdout, stderr=sys.stderr)


def gen_additional_properties(properties):
    return ",".join(map(lambda key_val: "{}={}".format(*key_val), properties.items()))


def gen_default_properties():
    param = dict(
        api_package="com.vroong.{}.api".format(service_name),
        model_package="com.vroong.{}.model".format(service_name)
    )
    param.update(extra_parameter)
    return param


def run_gradle(task):  # todo make parameters configurable.
    subprocess.check_call(args=["gradle", "-Papi_name={}".format(service_name),
                                "-Papi_version={}".format(version),
                                "-Pspring_boot_version=2.1.4.RELEASE", task],
                          cwd="/openapi-generator/gradle", stdout=sys.stdout, stderr=sys.stderr)


def npm_deploy(directory):
    fd = open((directory + "/.npmrc"), "w")
    print(f"@{github_owner}:registry={npm_repository}/{github_owner}\n{npm_repository.replace('https:', '')}/:_authToken={github_token}", file=fd)
    fd.flush()
    fd.close()

    subprocess.run(args=["npm", "install"], cwd=directory,
                   stdout=sys.stdout, stderr=sys.stderr)
    subprocess.run(args=["npm", "run", "build"],
                   cwd=directory, stdout=sys.stdout, stderr=sys.stderr)
    subprocess.run(args=["npm", "publish"], cwd=directory,
                   stdout=sys.stdout, stderr=sys.stderr)


def build_java_webclient():
    run_generator(
        service_name, spec_loc, "java", "webclient",
        api_package="com.example.{}.api".format(service_name),
        model_package="com.example.{}.model".format(service_name)
    )
    run_gradle(":java-webclient:publish")


def build_java_feign():
    run_generator(
        service_name, spec_loc, "java", "feign",
        **gen_default_properties(),
        additional_properties=gen_additional_properties({
            "dateLibrary": "java8",
            "hideGenerationTimestamp": "true",
            "useTags": "true"
        })
    )
    run_gradle(":java-feign:publish")


def build_spring_web():
    run_generator(
        service_name, spec_loc, "spring", "spring-boot",
        **gen_default_properties(),
        additional_properties=gen_additional_properties({
            "dateLibrary": "java8",
            "delegatePattern": "true",
            "useTags": "true"
        })
    )
    run_gradle(":spring:publish")


def build_spring_webflux():
    run_generator(
        service_name, spec_loc, "spring", "spring-boot",
        **gen_default_properties(),
        additional_properties=gen_additional_properties({
            "dateLibrary": "java8",
            "delegatePattern": "true",
            "useTags": "true",
            "reactive": "true"
        })
    )
    run_gradle(":spring-webflux:publish")


def build_typescript_fetch():
    run_generator(
        service_name, spec_loc, "typescript-fetch", None,
        # **gen_default_properties(), // todo remove model, api packages
        additional_properties=gen_additional_properties({
            "supportsES6": "true",
            "modelPropertyNaming": "original"
        })
    )
    service_dir = "/openapi-generator/" + service_name
    write_npm_pacakges_json(service_dir, f"{service_name}-fetch")
    npm_deploy(service_dir)


def build_typescript_axios():
    run_generator(
        service_name, spec_loc, "typescript-axios", None,
        # **gen_default_properties(), // todo remove model, api packages
        additional_properties=gen_additional_properties({
            "supportsES6": "true",
            "modelPropertyNaming": "original"
        })
    )
    service_dir = "/openapi-generator/" + service_name
    write_npm_pacakges_json(service_dir, f"{service_name}-axios")
    npm_deploy(service_dir)


def write_npm_pacakges_json(location, package_name):
    content = {
        "name": f"@{github_owner}/{reponame}",
        "version": version,
        "description": f"generated by oas sdk generator",
        "author": "actions-oas-sdk-generator",
        "main": "./dist/index.js",
        "typings": "./dist/index.d.ts",
        "scripts": {
            "build": "tsc",
            "prepare": "npm run build"
        },
        "devDependencies": {
            "typescript": "^2.4"
        },
        "publishConfig": {
            "registry": "https://npm.pkg.github.com/"
        },
        "repository": {
            "type": "git",
            "url": f"ssh://git@github.com/{github_repository}.git",
            "directory": f"packages/{package_name}"
        }
    }
    with open(location, "w") as f:
        f.write(content)
        f.flush()


BUILDERS = {
    "spring": build_spring_web,
    "spring-webflux": build_spring_webflux,
    "java-feign": build_java_feign,
    "java-webclient": build_java_webclient,
    "typescript-fetch": build_typescript_fetch,
    "typescript-axios": build_typescript_axios
}

builder = BUILDERS.get(generator)
if not builder:
    print("unknown generator {}, exit.".format(generator))
    # todo slack notification
    exit(1)

print("Start to Build SDK spec: {}, generator: {}".format(spec_loc, generator))
builder()
print(f"::set-output name=version::{version}")
