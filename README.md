# actions-oas-sdk-generator
Open Api Spec (oas) 파일을 다양항 서버/클라이언트 에서 사용하기 쉬운형태로 SDK 를 생성 / 배포 해 주는 액션입니다.
### 현재 지원중인 제너레이터
**버전**
* `4.1.3`

**종류**
* typescript fetch
* typescript axios
* ~~spring~~ (지원예정)
* ~~spring webflux~~ (지원예정)
* ~~java feign~~ (지원예정)
* ~~java webclient (of spring webflux)~~ (지원예정)

## Usage
### Pre-requisites
`.github/workflows` 에 `.yml` 확장자의 workflow를 만듭니다. 
open api spec 파일이 레포지토리 내에 존재해야합니다. (`.yml`, `.yaml`, `.json`)

### Inputs
* `generator` : 생성할 타깃 제너에이터를 입력합니다. 허용되는 입력값 - `typescript-fetch`, `typescript-axios`, `spring`, `spring-webflux`, `java-feign`, `java-webclient`
* `spec_location` : spec 파일의 위치입니다. 예: `src/main/swagger/api.yml`
* `github_token` : github packages 로 배포할 때 사용할 깃헙 token 예: `${{ secrets.GITHUB_TOKEN }}`

### Output
* `version` : 배포된 버전 명

## Example
```
on:
  push:
    paths:
    - 'src/main/swagger/api.yml'

name: Create OAS SDK

jobs:
  build:
    name: Create SDK
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@master
      - name: Generate and Publish
        id: generate_and_publish
        uses: meshkorea/actions-oas-sdk-generator@master
        with:
          generator: typescript-axios
          spec_location: src/main/swagger/api.yml
          github_token: ${{ secrets.GITHUB_TOKEN }}
```