document.onload = function() {
    initEmailAuth();
    initAnonAuth();
};

var initEmailAuth = function() {
    var emailBtn = document.getElementById('customBtnEmail');
    if (typeof emailBtn != 'undefined') {
        emailBtn.addEventListener('click', function(event) {
            var namePanel = document.getElementById('emailNameWrapper');
            namePanel.hidden = false;
        });
    }
    const formHandler = (e) => {
        e.preventDefault();
        localStorage.setItem("auth_choice", "email");
        // TODO: returnToRequestedPage();
    }
    var usernameInput = document.getElementById('usernameInput');
    var nameBtn = document.getElementById('btnEmailName');
    nameBtn.addEventListener('click', formHandler);
    document.getElementById('login-form').addEventListener('submit', formHandler);
}

var initAnonAuth = function() {
    var anonBtn = document.getElementById('customBtnAnon');
    if (typeof anonBtn != 'undefined') {
        anonBtn.addEventListener('click', function(event) {
            // check for saved name, use it
            var savedName = localStorage.getItem("display_name");
            if (savedName !== null) {
                localStorage.setItem("auth_choice", "anonymous");
                // TODO: returnToRequestedPage();
            } else { // if no passable name, ask for one
                var namePanel = document.getElementById('anonNameWrapper');
                namePanel.hidden = false;
            }
        });
    }
    const formHandler = (e) => {
        e.preventDefault();
        // remove extra spaces
        var displayName = usernameInput.value.replace(/\s+/g, " ").trim();
        localStorage.setItem("display_name", displayName);  // save for next use
        localStorage.setItem("auth_choice", "anonymous");
        // TODO: returnToRequestedPage();
    }
    var usernameInput = document.getElementById('usernameInput');
    var nameBtn = document.getElementById('btnAnonName');
    nameBtn.addEventListener('click', formHandler);
    document.getElementById('login-form').addEventListener('submit', formHandler);
}
