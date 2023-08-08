function returnToRequestedPage() {
    if (localStorage.getItem("request_uri")) {
        //redirect user to originally requested page
        location.href = localStorage.getItem("request_uri");
        localStorage.removeItem("request_uri");
    } else {
        //redirect user to root page
        location.href = `${window.location.origin}/scenes`;
    }
}

// ** New UI **

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

document.addEventListener('DOMContentLoaded', function () {   // document.ready() equiv
    // localStorage/cookie cleanup moved here from auth.js for canonical cleanup
    localStorage.removeItem('auth_choice'); // remove user auth
    localStorage.setItem('jwt', null); // remove filestore jwt

    // init
    const usernameContainer = document.getElementById('usernameContainer');
    const anonBtn = document.getElementById('anonBtn');
    const googleBtn = document.getElementById('googleBtn');
    const providerSelect = document.getElementById('provider');
    providerSelect.selectedIndex = 0; // Reset for history-nav
    providerSelect.addEventListener('change', ({target}) => {
        switch (target.value) {
            case 'google':
                hideEls([usernameContainer, anonBtn]);
                showEl(googleBtn);
                break;
            case 'anon':
                showEl(usernameContainer);
                hideEls([googleBtn]);
                showEl(anonBtn);
                break;
            default:
            //
        }
    });
    const nameRegex = '^(?=[^A-Za-z]*[A-Za-z]{2,})[ -~]*$';
    const usernameInput = document.getElementById('usernameInput');
    usernameInput.setAttribute('pattern', nameRegex);

    if (localStorage.getItem('display_name')) {
        usernameInput.value = localStorage.getItem('display_name');
        usernameInput.focus();
    }

    // ** Anon Auth Init
    const re = new RegExp(nameRegex);
    const anonFormHandler = (e) => {
        e.preventDefault();
        // validate
        if (re.test(usernameInput.value)) {
            // remove extra spaces
            const displayName = usernameInput.value.replace(/\s+/g, ' ').trim();
            localStorage.setItem('display_name', displayName);  // save for next use
            localStorage.setItem('auth_choice', 'anonymous');
            returnToRequestedPage();
        }
    };
    document.getElementById('loginForm').addEventListener('submit', anonFormHandler);
    providerSelect.dispatchEvent(new Event('change')); // Manually trigger selection effects for default
});
