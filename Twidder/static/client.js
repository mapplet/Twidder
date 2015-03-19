var json;
var welcomeView = "welcomeView";
var profileView = "profileView";
var home = "home";
var account = "account";
var browse = "browse";
var websocket = null;

displayView = function(){
    // the code required to display a view
    console.log('# Refreshed page.');
    if (localStorage.token) {

        console.log('  > User is signed in.');

        setView(profileView, home);
        tokenIsValid = setUserData();
        initWebSocket();

        if (location.hash == "#account") {
	        setView(profileView, account);
	    }
	    else if (location.hash == "#browse") {
	        setView(profileView, browse);
	    }
	    else if (validateEmail(location.hash.substr(1))) {
	        setView(profileView, browse);
	        var email = location.hash.substr(1);
	        browseSearch(email);
	    }
    }

    else {
        console.log('  > User is NOT signed in.');
        setView(welcomeView);
    }
};

function onOpen(msg) {
    console.log("WebSocket: CONNECTED");
    if (localStorage.token)
        websocket.send(localStorage.token);
}
function onClose(msg) {
    console.log("WebSocket: DISCONNECTED");
    if (localStorage.token)
        console.log('# Will remove token from localStorage.');
        localStorage.removeItem('token');
        setView(welcomeView);
}
function onMessage(msg) {
    console.log("WebSocket: RECEIVED MSG(\"" + msg + "\")");
    // websocket.close();
}
function onError(msg) {
    console.log("WebSocket: ERROR(\"" + msg.data + "\")");
}

window.onload = function(){
    //code that is executed as the page is loaded.
    //You shall put your own custom code here.
    //window.alert("Hello TDDD97!");
    displayView();
};

setView = function (view, tab){

    // console.log('Entering setView.');

    document.getElementById("main").innerHTML = document.getElementById(view).innerHTML;
    if (localStorage.token) {
        if (tab) {
            console.log('# Changed tab to: ' + tab);
            activateView(tab);
        }
        else
            activateView(home);
    }
};

printWarning = function(message, viewIn){
    var view;
    if (viewIn == "welcomeView")
	view = document.getElementById("warning");
    else if (viewIn == "home")
	view = document.getElementById("warningHome");
    else if (viewIn == "browse")
	view = document.getElementById("warningBrowse");
    else if (viewIn == "account")
	view = document.getElementById("warningAccount");

    view.style.display = "block";
    view.textContent = message;
};

initWebSocket = function() {
    if ("WebSocket" in window) {
        websocket = new WebSocket("ws://" + document.domain + ":5000/socket_connect");
        websocket.onopen = onOpen;
        websocket.onmessage = function(msg) { onMessage(msg); };
        websocket.onclose = function(msg) { onClose(msg); };
        websocket.onerror = function(msg) { onError(msg); };
    }
    else {
        console.log("WebSocket not supported");
    }
};

xmlHttpRequest = function(success, failure, route, formData){

    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function(){

        // console.log("Readystate: "+xmlhttp.readyState);
        // console.log("Status: "+xmlhttp.status);

        if (xmlhttp.readyState == 4 && xmlhttp.status == 200){

            // console.log("Response:\n"+xmlhttp.responseText);
            json = JSON.parse(xmlhttp.responseText);

            if (json.success){
                success();
                return true;
            }
            else {
                failure();
                return false;
            }
        }
    };

    xmlhttp.open("POST", route, true);
    xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
    xmlhttp.send(formData);
    return false;
};

signIn = function(email, password){

    console.log("Entering signIn");

    success = function(){
        localStorage.token = json.data;
        setView(profileView, home);
        setUserData();

        initWebSocket();
    };
    failure = function(){
        printWarning(json.message, welcomeView);
        document.forms["signInForm"]["password"].value = "";
    };
    var route = "sign_in";
    var formData = "email="+email+"&password="+password;
    return xmlHttpRequest(success, failure, route, formData);
};

setUserData = function(){

    success = function(){
        document.getElementById("fullname").innerHTML = json.data.firstname + " " + json.data.lastname + ", " + json.data.gender;
        document.getElementById("fulladdress").innerHTML = json.data.country + ", " + json.data.city;
        document.getElementById("fullcontact").innerHTML = json.data.email;
        updateWall("messages");
    };
    failure = function(){
        printWarning(json.message, profileView);
    };
    var route = "get_user_data";
    var formData = "token="+localStorage.token;
    return xmlHttpRequest(success, failure, route, formData);
};

signUp = function(fname, lname, gender, city, country, email, password, rePassword){

    console.log("Entering signUp");

    if (!validateEmail(email)){
	printWarning("Invalid format of email.", "welcomeView");
	return false;
    }
    else if (!validatePassword(password)){
	printWarning("Password must be at least 6 characters.", "welcomeView");
	return false;
    }
    else if (password != rePassword){
	printWarning("Passwords does not match.", "welcomeView");
	return false;
    }
    else if (fname == "" || lname == "" || gender == "" || city == "" || country == ""){
	printWarning("All fields must be filled in.", "welcomeView");
	return false;
    }
    else {

        success = function(){
            signIn(email, password);
        };
        failure = function(){
            printWarning(json.message, welcomeView);
            document.forms["signUpForm"]["email"].value = "";
            document.forms["signUpForm"]["password"].value = "";
            document.forms["signUpForm"]["repassword"].value = "";
            document.forms["signUpForm"]["email"].focus();
        };
        var route = "sign_up";
        var formData = "firstname="+fname+"&lastname="+lname+"&gender="+gender+"&city="+city+"&country="+country+"&email="+email+"&password="+password;
        return xmlHttpRequest(success, failure, route, formData);
    }
};

validateEmail = function(mail) {
    return (/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(mail));
};

validatePassword = function(password){
    return (password.length >= 6)
};

postMessage = function(myWall, message){

    console.log("Entering postMessage");

    if(message.trim() == "")
    {
	    printWarning("Empty messages are not allowed.", "home");
	    return false;
    }

    var success = null;
    var failure = null;
    var route = "post_message";
    var formData = "token="+localStorage.token+"&content="+message;


    if (myWall) {
        success = function(){
            updateWall("messages");
            document.getElementById("walltextbox").value = "";
        };
        failure = function(){
            printWarning(json.message, home);
        };
    }
    else {
        success = function(){

            updateWall("userMessages");
            document.getElementById("browsewalltextbox").value = "";
        };
        failure = function(){
            printWarning(json.message, browse);
        };
        var email = location.hash.substr(1);
        formData += "&toEmail="+email;
    }


    return xmlHttpRequest(success, failure, route, formData);
};

changePassword = function(oldPassword, newPassword, reNewPassword){

    console.log("Entering changePassword");

    if (!validatePassword(oldPassword) || !validatePassword(newPassword)){
	    printWarning("Passwords must be at least 6 characters.", "account");
        document.forms["changePasswordForm"].reset();
        document.forms["changePasswordForm"]["oldpassword"].focus();
	    return false;
    }
    else if (newPassword != reNewPassword){
	    printWarning("Passwords does not match.", "account");
        document.forms["changePasswordForm"]["newpassword"].value = "";
        document.forms["changePasswordForm"]["renewpassword"].value = "";
        document.forms["changePasswordForm"]["newpassword"].focus();
	    return false;
    }
    else {

        success = function(){
            printWarning(json.message, "account");
            document.forms["changePasswordForm"].reset();
            document.forms["changePasswordForm"]["oldpassword"].focus();
        };
        failure = function(){
            printWarning(json.message, "account");
            document.forms["changePasswordForm"].reset();
	        document.forms["changePasswordForm"]["oldpassword"].focus();
        };
        route = "change_password";
        formData = "token="+localStorage.token+"&oldPassword="+oldPassword+"&newPassword="+newPassword;
        return xmlHttpRequest(success, failure, route, formData);
    }
};

signOut = function(){

    console.log("Entering signOut");

    if (localStorage.token)
    {
        success = function(){
            location.assign(location.href.split('#')[0]);
            localStorage.removeItem("token");
            websocket.close();
        };
        failure = function(){
            printWarning(json.message, "account");
        };
        var route = "sign_out";
        var formData = "token="+localStorage.token;
        return xmlHttpRequest(success, failure, route, formData);
    }
    else
        printWarning("You are not signed in on this device anymore.", "account");
	    return false;
};

browseSearch = function(email){

    console.log("Entering browseSearch");

    location.href = "#"+email;

    success = function(){
        document.getElementById("browseContent").style.display = "block";
	    document.getElementById("userFullname").innerHTML = json.data.firstname + " " + json.data.lastname + ", " + json.data.gender;
	    document.getElementById("userFulladdress").innerHTML = json.data.country + ", " + json.data.city;
	    document.getElementById("userFullcontact").innerHTML = json.data.email;

	    updateWall("userMessages", email);
    };
    failure = function(){
        printWarning(json.message, "browse");
    };
    var route = "get_user_data/"+email;
    var formData = "token="+localStorage.token;

    return xmlHttpRequest(success, failure, route, formData)
};

activateView = function(type){

    console.log("Entering activateView");

    var tabs = ["home", "browse", "account"];
    var links = ["linkHome", "linkBrowse", "linkAccount"];
    var count = tabs.length;
    for (i = 0; i<count; ++i)
    {
	    if (tabs[i]!=type)
	    {
	        document.getElementById(links[i]).style.color = "#4682B4";
	        document.getElementById(links[i]).style.pointerEvents = "auto";
	        document.getElementById(tabs[i]).style.display = "none";
	    }
	    else if (tabs[i]==type)
	    {
	        document.getElementById(links[i]).style.color = "#CCC";
	        document.getElementById(links[i]).style.pointerEvents = "none";
	        document.getElementById(tabs[i]).style.display = "block";
	    }
    }

    return true;
};

updateWall = function(wall){

    console.log("Entering updateWall");

    var messagesNode = document.getElementById(wall);
    var messages = null;

    success = function(){
        messages = json.data;

        while (messagesNode.firstChild)
        {
            messagesNode.removeChild(messagesNode.firstChild);
        }

        for (i = messages.length-1; i >= 0; --i) {
	        var newElement = document.createElement('div');
	        newElement.style.width = "430px";
	        newElement.style.paddingBottom = "10px";
	        newElement.innerHTML = '<p style="font-style: italic; margin-bottom: 4px;">'+messages[i].timestamp+"</p>"+'\n'+'<h3 style="margin-bottom: 4px; margin-top: 0px;">' + messages[i].sender + ' wrote:</h3>' + messages[i].message;
	        document.getElementById(wall).appendChild(newElement);
	    }
    };
    failure = function(){
        document.getElementById(wall).innerHTML = '<p style="font-style: italic; font-size: 14px; color: #555; text-align: center;">Nothing here :(</p>';
    };
    var route = "get_user_messages";

    var email = location.hash.substr(1);
    if (email && validateEmail(email))
        route += "/"+email;
    var formData = "token="+localStorage.token;


    return xmlHttpRequest(success, failure, route, formData);
};