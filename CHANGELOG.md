# Changelog


## [2.2.0](https://github.com/arenaxr/arena-account/compare/v2.1.2...v2.2.0) (2026-02-05)


### Features

* **persist:** replaced persist O(n2) REST calls with O(1) PyMongo calls ([6d38239](https://github.com/arenaxr/arena-account/commit/6d382391875ffed2c6f771ac5267fc66961fc7bf))


### Bug Fixes

* **allauth:** ensure generated site entries in db are saved correctly ([f97d822](https://github.com/arenaxr/arena-account/commit/f97d82222a8a1fa9c1edac4251a076bc31ca39ba))
* **allauth:** remomve conflicting db social apps from legacy allauth ([6bf521c](https://github.com/arenaxr/arena-account/commit/6bf521c02496e4b6214159d643254742d7b24e2f))
* **jwt:** allow large token in response, but limit large token in cookie. Closes [#115](https://github.com/arenaxr/arena-account/issues/115) ([2412865](https://github.com/arenaxr/arena-account/commit/24128656afb04c898ec52145a51e51b8c7dd2346))
* **namespace:** update namespace deletes to include objects, increase delete warnings ([2990d75](https://github.com/arenaxr/arena-account/commit/2990d754d7a5b8a6286ab3ed3350b7fcb77821c6))
* **navbar:** updated header links for programs, docs ([b24fb86](https://github.com/arenaxr/arena-account/commit/b24fb86bd89dca1afc0e8226890089ed67a882d0))
* **persist:** use mongo concat to avoid reparsing scenes queries ([ed95d29](https://github.com/arenaxr/arena-account/commit/ed95d29402fddedee5bee5c8fb361551f4ae79a2))
* **REST:** reduce my_scenes endpoint query complexity with python sets and mongo db direct calls ([7087f3f](https://github.com/arenaxr/arena-account/commit/7087f3f9364a1e671ed7ac63581029f984dafb57))
* **scenes:** fixed my_scenes sort to handle None values safely ([03c5898](https://github.com/arenaxr/arena-account/commit/03c58981d619a883c5fd70a893cf7ccbb01549ad))
* **scenes:** fixed my_scenes sort to handle None values safely ([9208b85](https://github.com/arenaxr/arena-account/commit/9208b85b41fc89ac0cec288f4315162964a12656))
* **scenes:** remove legacy redundant default scenes from db ([3151ffa](https://github.com/arenaxr/arena-account/commit/3151ffa044fb1927fe63a887cd05a0b1e66d5bed))

## [2.1.2](https://github.com/arenaxr/arena-account/compare/v2.1.1...v2.1.2) (2025-12-08)


### Bug Fixes

* **admin:** allow admin to sort by date, name, summary ([2c7d75f](https://github.com/arenaxr/arena-account/commit/2c7d75f7377ee23b17245784722e9a97ea288f78))
* **allauth:** upgrade allauth v62 removes custom form validation ([84909d9](https://github.com/arenaxr/arena-account/commit/84909d93891892041c4f01d2bbc75249924d9c9e))
* **google:** migrate to login post only allauth v56 ([a8dceaf](https://github.com/arenaxr/arena-account/commit/a8dceaf2cca8779ef1f80a2d7448514a6bd4e9d9))
* **mqtt:** allow subscription by namespace and scene viewer perms ([dcf9543](https://github.com/arenaxr/arena-account/commit/dcf9543733057aef6c0b3973486ea93f60f98bc2))

## [2.1.1](https://github.com/arenaxr/arena-account/compare/v2.1.0...v2.1.1) (2025-09-10)


### Bug Fixes

* **django:** upgrade django to 4.2.24, bump most minor deps ([9d291a6](https://github.com/arenaxr/arena-account/commit/9d291a66bdad41c03048b18599dd3f6313f571f6))

## [2.1.0](https://github.com/arenaxr/arena-account/compare/v2.0.2...v2.1.0) (2025-01-31)


### Features

* **namespace:** allow editors/viewers by namespace ([d785641](https://github.com/arenaxr/arena-account/commit/d7856411df6e7233ebf0609f56556bc3aa0fe326))

## [2.0.2](https://github.com/arenaxr/arena-account/compare/v2.0.1...v2.0.2) (2024-12-17)


### Bug Fixes

* **mqtt:** refactor programs scope ([657342a](https://github.com/arenaxr/arena-account/commit/657342a7f27d73adcda4e948bf27202fdd5ed69a))

## [2.0.1](https://github.com/arenaxr/arena-account/compare/v2.0.0...v2.0.1) (2024-11-19)


### Bug Fixes

* **mqtt:** add environmentid request for 'e' host permissions ([73ed411](https://github.com/arenaxr/arena-account/commit/73ed41136841eed337f861f2e5ca82c57d1f1436))
* **mqtt:** add requirement renderfusion perms with context request ([6264c11](https://github.com/arenaxr/arena-account/commit/6264c11528001cc36ada7c87ac2c82bda9b29155))
* **mqtt:** allow scene editors write access to public programtopics ([78b3d89](https://github.com/arenaxr/arena-account/commit/78b3d8964172ae6b9355296c343d48ceb257903a))
* **mqtt:** consolidate token perms by message type and scene write ([#108](https://github.com/arenaxr/arena-account/issues/108)) ([6ba6cad](https://github.com/arenaxr/arena-account/commit/6ba6cad0514504b6fc17c04d03c02a4a1c50a1ea))

## [2.0.0](https://github.com/arenaxr/arena-account/compare/v1.3.0...v2.0.0) (2024-11-07)


### ⚠ BREAKING CHANGES

* Refactored topic structure for more granular flow and access ([#100](https://github.com/arenaxr/arena-account/issues/100))

### Features

* Refactored topic structure for more granular flow and access ([#100](https://github.com/arenaxr/arena-account/issues/100)) ([ac27f8e](https://github.com/arenaxr/arena-account/commit/ac27f8ec11479b1949cd28ee8f5a7f58a3ec331a))


### Bug Fixes

* **mqtt:** require userClient in topic for all scene messages ([#107](https://github.com/arenaxr/arena-account/issues/107)) ([07a98a2](https://github.com/arenaxr/arena-account/commit/07a98a2b42b05ab430bcf4158e0c37795b966dce))

## [1.3.0](https://github.com/arenaxr/arena-account/compare/v1.2.2...v1.3.0) (2024-09-20)


### Features

* **auth:** allow device auth flow google id verification ([3f5d567](https://github.com/arenaxr/arena-account/commit/3f5d5675d1f8c65aeeedc777654906460707f8ae))

## [1.2.2](https://github.com/arenaxr/arena-account/compare/v1.2.1...v1.2.2) (2024-05-06)


### Bug Fixes

* **filestore/persist:** add api rest connection timeouts ([d899982](https://github.com/arenaxr/arena-account/commit/d8999826475b56c63bf7cdb692e4450f23a9629f))
* **filestore:** check for failed token before parsing ([4a03bf9](https://github.com/arenaxr/arena-account/commit/4a03bf9ff7bd8656f0bc67c7dcf902edf96eadd3))
* **filestore:** correct staff scope for new user login ([79b0621](https://github.com/arenaxr/arena-account/commit/79b06210beb6e982ec210befd0b6146c184a1902))
* **filestore:** ensure user does not exist before renewing login ([08110e7](https://github.com/arenaxr/arena-account/commit/08110e781eef94240918baceadb8100dc01fb526))
* **filestore:** handle django allauth oauth pass reset ([7e8aadf](https://github.com/arenaxr/arena-account/commit/7e8aadf89d4a894b0e59c4b7c8622fd6af8c30be))
* **filestore:** minimize api calls per login ([9c8c74b](https://github.com/arenaxr/arena-account/commit/9c8c74b8a31ba52be919f7282e437af9cebd0e60))
* **filestore:** prevent code 500 for anonymous login ([b702279](https://github.com/arenaxr/arena-account/commit/b702279378a43fb37296bce5d6bdafc17ab8c65c))
* **filestore:** use correct scope at new user insert for auto create user dir ([577b8e1](https://github.com/arenaxr/arena-account/commit/577b8e111114ff210dbd5a43a197ead5c55cfece))
* **filestore:** use http get for fs login per filebrowser v2.22.4 ([09505e4](https://github.com/arenaxr/arena-account/commit/09505e4388bb7c99c6bea0ae8940f06ade90de8f))
* make release please trigger other workflows (using a PAT) ([10058e7](https://github.com/arenaxr/arena-account/commit/10058e78d0b37a4654eea528123df88f3a038a97))

## [1.2.1](https://github.com/arenaxr/arena-account/compare/v1.2.0...v1.2.1) (2024-04-15)


### Bug Fixes

* bump docker python version ([c258469](https://github.com/arenaxr/arena-account/commit/c25846950ed645b2e59ae12de65381b682fcbe8e))
* upgrade to django 3.2, retaining AutoField key index size ([99d47fc](https://github.com/arenaxr/arena-account/commit/99d47fc465b49089a91f1dfc1d3d806b2b14a4bc))

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
