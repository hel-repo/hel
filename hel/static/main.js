var mainMenu = null;
var logInForm = null;
var regForm = null;

window.onload = function() {
  mainMenu = document.getElementById("auth-menu");
  logInForm = document.getElementById("log-in-form");
  regForm = document.getElementById("register-form");
}

function switchTo(menu) {
  mainMenu.className = "hidden";
  logInForm.className = "hidden";
  regForm.className = "hidden";
  switch (menu) {
    case "main":
      mainMenu.className = "";
      break;
    case "register":
      regForm.className = "";
      break;
    case "login":
      logInForm.className = "";
      break;
  }
}
