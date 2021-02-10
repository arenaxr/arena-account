'use strict';

document.addEventListener('DOMContentLoaded', function () {   // document.ready() equiv

    // Rudimentary routing based on location hash
    window.addEventListener('hashchange', function () {
        const validRoutes = [
            '#sceneSelect',
            '#cloneScene',
        ];
        const routePage = validRoutes.includes(window.location.hash) ? window.location.hash : '#sceneSelect';
        const pageEl = document.querySelector(routePage);
        hideEls(document.querySelectorAll(`.routePage:not(${routePage})`));
        showEl(pageEl, true);
        pageEl.dispatchEvent(new Event('routePageLoaded'));
    }, false);

    document.getElementById('closeCloneScene').addEventListener('click', () => {
        changePage('#sceneSelect');
    })

    function showEl(el, flex = false) {
        const showClass = flex ? 'd-flex' : 'd-block';
        el.classList.add(showClass);
        el.classList.remove('d-none');
    }

    function hideEls(els, flex = false) {
        const showClass = flex ? 'd-flex' : 'd-block';
        for (let el of els) {
            el.classList.add('d-none');
            el.classList.remove(showClass);
        }
    }

    function changePage(page = 'sceneSelect') {
        if (window.location.hash !== page) {
            window.location.hash = page;
        }
    }

    const userSceneInput = document.getElementById('userSceneInput');
    const userSceneUrl = document.getElementById('userSceneUrl');

    const enterUserSceneBtn = document.getElementById('enterUserSceneBtn');
    const cloneUserSceneBtn = document.getElementById('cloneUserSceneBtn');
    const deleteUserSceneBtn = document.getElementById('deleteUserSceneBtn');
    const copyUserSceneUrlBtn = document.getElementById('copyUserSceneUrlBtn')

    const publicSceneInput = document.getElementById('publicSceneInput');
    const publicSceneUrl = document.getElementById('publicSceneUrl');

    const enterPublicSceneBtn = document.getElementById('enterPublicSceneBtn');
    const clonePublicSceneBtn = document.getElementById('clonePublicSceneBtn');

    window.userSceneId = '';
    window.publicSceneId = '';
    window.cloneSceneId = '';

    const toggleUserSceneButtons = (toggle) => {
        [enterUserSceneBtn, cloneUserSceneBtn, deleteUserSceneBtn, copyUserSceneUrlBtn].forEach((btn) => {
            toggle ? btn.classList.remove('disabled') : btn.classList.add('disabled')
        })
    }
    const togglePublicSceneButtons = (toggle) => {
        [enterPublicSceneBtn, clonePublicSceneBtn].forEach((btn) => {
            toggle ? btn.classList.remove('disabled') : btn.classList.add('disabled')
        })
    }

    userSceneInput.addEventListener('change', checkUserSceneInput)
    userSceneInput.addEventListener('keyup', checkUserSceneInput)
    publicSceneInput.addEventListener('change', checkPublicSceneInput)
    publicSceneInput.addEventListener('keyup', checkPublicSceneInput)

    function checkUserSceneInput(e) {
        if (e.target.value &&
            [...document.getElementById('userSceneDatalist').options].findIndex((o) => o.value === e.target.value) !== -1) {
            window.userSceneId = e.target.value;
            userSceneUrl.value = `${window.location.protocol}//${window.location.hostname}/${e.target.value}`
            deleteUserSceneBtn.value = e.target.value;
            toggleUserSceneButtons(true);
        } else {
            window.userSceneId = '';
            userSceneUrl.value = 'No valid scene selected';
            toggleUserSceneButtons(false);
        }
    }

    function checkPublicSceneInput(e) {
        if (e.target.value &&
            [...document.getElementById('publicSceneDatalist').options].findIndex((o) => o.value === e.target.value) !== -1) {
            window.publicSceneId = e.target.value;
            publicSceneUrl.value = `${window.location.protocol}//${window.location.hostname}/${e.target.value}`
            togglePublicSceneButtons(true);
            console.log("valid public", e.target.value)
        } else {
            window.publicSceneId = '';
            publicSceneUrl.value = '';
            togglePublicSceneButtons(false);
            console.log("invalid public", e.target.value)
        }
    }


    publicSceneInput.addEventListener('change', (e) => {
        if (e.target.value) {
            publicSceneUrl.value = `${window.location.protocol}//${window.location.hostname}/${e.target.value}`
        } else {
            publicSceneUrl.value = "";
        }
    });
    copyUserSceneUrlBtn.addEventListener('click', () => {
        userSceneUrl.select();
        userSceneUrl.setSelectionRange(0, 99999); /* For mobile devices */
        document.execCommand("copy");
    })
    enterUserSceneBtn.addEventListener('click', () =>
        window.location = userSceneUrl.value
    )
    enterPublicSceneBtn.addEventListener('click', () =>
        window.location = publicSceneUrl.value
    )

    deleteUserSceneBtn.addEventListener('click', (e) => {
        return confirm(`Are you sure you want to delete ${e.target.value}?`);
    })

    cloneUserSceneBtn.addEventListener('click', () => {
        window.cloneSceneId = window.userSceneId;
        resetCloneScene();
        changePage('cloneScene');
    });

    clonePublicSceneBtn.addEventListener('click', () => {
        window.cloneSceneId = window.publicSceneId;
        resetCloneScene();
        changePage('cloneScene');
    });


    /*  *********************** */

    const newSceneNameInput = document.getElementById('newSceneNameInput');
    const doCloneSceneBtn = document.getElementById('doCloneSceneBtn');
    const cloneSceneUrl = document.getElementById('cloneSceneUrl');
    const sourceScene = document.getElementById('sourceScene');

    function resetCloneScene() {
        sourceScene.value = window.cloneSceneId;
        newSceneNameInput.value = "";
        document.getElementById('cloneSceneCreated').classList.add('d-none');
        document.getElementById('doCloneSceneContainer').classList.remove('d-none');
    }

    newSceneNameInput.addEventListener('keyup', (e) => {
        if (e.target.value) {
            doCloneSceneBtn.classList.remove('disabled');
        } else {
            doCloneSceneBtn.classList.add('disabled');
        }
    })

    document.getElementById('doCloneSceneBtn').addEventListener('click', () => {
        const [namespace, sceneId] = sourceScene.value.split("/")
        axios.post(`/persist/${window.username}/${newSceneNameInput.value}`, {
            action: 'clone',
            namespace,
            sceneId,
        }).then((res) => {
            Swal.fire('Clone success!', `${res.data.objectsCloned} objects cloned into new scene`, 'success');
            cloneSceneUrl.value = `${window.location.protocol}//${window.location.hostname}/${newSceneNameInput.value}`
            document.getElementById('doCloneSceneContainer').classList.add('d-none');
            document.getElementById('cloneSceneCreated').classList.remove('d-none');
            newSceneNameInput.setAttribute('readonly', 'readonly')
        }).catch((err) => {
            Swal.fire('Scene Clone Failed!', `Something went wrong!`, 'warning');
            console.log(err);
        });
    })

    const copyCloneSceneUrlBtn = document.getElementById('copyCloneSceneUrlBtn')
    copyCloneSceneUrlBtn.addEventListener('click', () => {
        cloneSceneUrl.select();
        cloneSceneUrl.setSelectionRange(0, 99999); /* For mobile devices */
        document.execCommand("copy");
    })

    document.getElementById('enterCloneSceneBtn').addEventListener('click', () => {
        window.location = cloneSceneUrl.value;
    })


    window.dispatchEvent(new Event('hashchange')); // Manually trigger initial hash routing
});