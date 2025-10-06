// script.js

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");
  const loginBox = document.getElementById("login-box");
  const registerBox = document.getElementById("register-box");
  const showRegister = document.getElementById("show-register");
  const showLogin = document.getElementById("show-login");

  // Toggle forms
  showRegister.addEventListener("click", (e) => {
    e.preventDefault();
    loginBox.classList.add("hidden");
    registerBox.classList.remove("hidden");
  });

  showLogin.addEventListener("click", (e) => {
    e.preventDefault();
    registerBox.classList.add("hidden");
    loginBox.classList.remove("hidden");
  });

  // Handle register
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = {
      name: document.getElementById("regName").value,
      email: document.getElementById("regEmail").value,
      password: document.getElementById("regPassword").value,
    };

    const res = await fetch("http://127.0.0.1:5000/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const result = await res.json();
    alert(result.message);
    if (res.ok) {
      registerBox.classList.add("hidden");
      loginBox.classList.remove("hidden");
    }
  });

  // Handle login
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = {
      email: document.getElementById("loginEmail").value,
      password: document.getElementById("loginPassword").value,
    };

    const res = await fetch("http://127.0.0.1:5000/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const result = await res.json();
    if (res.ok) {
      localStorage.setItem("token", result.token);
      window.location.href = "dashboard.html";
    } else {
      alert(result.message);
    }
  });
});
