window.onload = function() {
  switchTo("main")
}

function switchTo(form) {
  $("#auth-menu").hide();
  $("#log-in-form").hide();
  $("#register-form").hide();
  switch (form) {
    case "main":
      $("#auth-menu").show();
      break;
    case "register":
      $("#register-form").show();
      break;
    case "login":
      $("#log-in-form").show();
      break;
  }
}
