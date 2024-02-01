# Changelog

## [1.2.0](https://github.com/arenaxr/arena-account/compare/v1.1.5...v1.2.0) (2024-02-01)


### Features

* **filestore:** allow remote filestore auth with id token context ([#86](https://github.com/arenaxr/arena-account/issues/86)) ([c468bb0](https://github.com/arenaxr/arena-account/commit/c468bb09dab1d28f8b412c5c91407a11ec346b28))

## [1.1.5](https://github.com/arenaxr/arena-account/compare/v1.1.4...v1.1.5) (2023-12-14)


### Bug Fixes

* **mqtt:** Add /env/ topic tree that mirrors /s/ ([4f3c224](https://github.com/arenaxr/arena-account/commit/4f3c224b18be637ef0b1737271ff53d13b468a54))

## [1.1.4](https://github.com/arenaxr/arena-account/compare/v1.1.3...v1.1.4) (2023-10-11)


### Bug Fixes

* **login:** fixed missing validation feedback for anonymous display name ([6b364bd](https://github.com/arenaxr/arena-account/commit/6b364bd72dbfb3e190bd11ff79200493e30c6cd5))

## [1.1.3](https://github.com/arenaxr/arena-account/compare/v1.1.2...v1.1.3) (2023-09-05)


### Bug Fixes

* **auth:** return is_staff state in user_state endpoint ([9cfe31b](https://github.com/arenaxr/arena-account/commit/9cfe31b188aae04146ddaefcda6ae8a5ce984039))
* **fs:** always check scope on filestore login ([b73470a](https://github.com/arenaxr/arena-account/commit/b73470a1ebf29b93e5ad1d1bfcb78dbcb5b5f986))
* **fs:** improve fs user scope lookup ([f6865c9](https://github.com/arenaxr/arena-account/commit/f6865c9514cbedd756804bc1d4eaf32e29e139bf))
* **fs:** onl;y use relative scope for all users ([9ff645d](https://github.com/arenaxr/arena-account/commit/9ff645d05c76d6cdbdbad60ec87adee7396d9185))
* **fs:** revoke filestore auth implicitly on logout ([4f9fffa](https://github.com/arenaxr/arena-account/commit/4f9fffa7fa18710c4a9d06cf457315f521046f01))
* make all login fields focusable ([9eb5a36](https://github.com/arenaxr/arena-account/commit/9eb5a36324ef8a956006b2c6940ac6745e5a1b3b))
* move fs logout to site logout ([3abea7e](https://github.com/arenaxr/arena-account/commit/3abea7e5baeb1d7e9faef458ad6315e5458b3d08))
* show all auth choices by default equal weight ([#78](https://github.com/arenaxr/arena-account/issues/78)) ([0f8e3e7](https://github.com/arenaxr/arena-account/commit/0f8e3e743c3eae4841b6d7e5c3d63195c2399b39))
* upgrade pyyaml to new supported config ([71e410b](https://github.com/arenaxr/arena-account/commit/71e410b86ed00263d5aadc8cd2a996c1264e5987))

## [1.1.2](https://github.com/arenaxr/arena-account/compare/v1.1.1...v1.1.2) (2023-07-10)


### Bug Fixes

* add new orchestrator endpoint ([0c29eba](https://github.com/arenaxr/arena-account/commit/0c29ebaf23f1a445a5dd543315dfacb903e80ee1))
* **mqtt:** simplify public scene reads ([21422a4](https://github.com/arenaxr/arena-account/commit/21422a46f41885c36e3ad9a98376d86d32764563))

## [1.1.1](https://github.com/arenaxr/arena-account/compare/v1.1.0...v1.1.1) (2022-07-20)


### Bug Fixes

* device token generation crash ([4f17826](https://github.com/arenaxr/arena-account/commit/4f178262e93dc937cc4c21901f8f1f990b09d1be))

## [1.1.0](https://github.com/conix-center/arena-account/compare/v1.0.1...v1.1.0) (2022-07-14)


### Features

* **auth:** Add ability to remove user interaction ([#65](https://github.com/conix-center/arena-account/issues/65)) ([c487b7f](https://github.com/conix-center/arena-account/commit/c487b7fb0c2b3359c07314652499060eabdbfa5b))


### Bug Fixes

* add versions link to header ([e09d057](https://github.com/conix-center/arena-account/commit/e09d05793139e7ee3308be0d972fe57aae5a8861))
* redirect logged in user to /scenes ([7ab1d0b](https://github.com/conix-center/arena-account/commit/7ab1d0bd62fb717629fdacd365a6c3a33868d392))
