document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const messageDiv = document.getElementById("message");

  const categoryFilters = document.getElementById("category-filters");
  const dayFilters = document.getElementById("day-filters");
  const timeFilters = document.querySelector(".time-filters");
  const searchBox = document.getElementById("activity-search");
  const searchButton = document.getElementById("search-button");

  const registrationModal = document.getElementById("registration-modal");
  const closeModalBtn = registrationModal.querySelector(".close-modal");
  const signupForm = document.getElementById("signup-form");
  const modalActivityName = document.getElementById("modal-activity-name");
  const hiddenActivityInput = document.getElementById("activity");

  const loginModal = document.getElementById("login-modal");
  const closeLoginModalBtn = loginModal.querySelector(".close-login-modal");
  const loginButton = document.getElementById("login-button");
  const logoutButton = document.getElementById("logout-button");
  const loginForm = document.getElementById("login-form");
  const loginMessage = document.getElementById("login-message");
  const userInfo = document.getElementById("user-info");
  const displayNameSpan = document.getElementById("display-name");

  let teacherUsername = null;

  // ---------------------------
  // Utility functions
  // ---------------------------
  function showMessage(text, type = "success") {
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove("hidden");
    setTimeout(() => messageDiv.classList.add("hidden"), 5000);
  }

  function openModal(modal) {
    modal.classList.remove("hidden");
  }

  function closeModal(modal) {
    modal.classList.add("hidden");
  }

  // ---------------------------
  // Fetch Activities
  // ---------------------------
  async function fetchActivities(filters = {}) {
    try {
      let url = "/activities";
      const params = new URLSearchParams();

      if (filters.day) params.append("day", filters.day);
      if (filters.start_time) params.append("start_time", filters.start_time);
      if (filters.end_time) params.append("end_time", filters.end_time);

      if ([...params].length > 0) {
        url += "?" + params.toString();
      }

      const response = await fetch(url);
      const activities = await response.json();

      activitiesList.innerHTML = "";

      Object.entries(activities).forEach(([name, details]) => {
        const card = document.createElement("div");
        card.className = "activity-card";

        const spotsLeft = details.max_participants - details.current_count;

        card.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule_details?.days?.join(", ")} ${details.schedule_details?.start_time || ""}-${details.schedule_details?.end_time || ""}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <button class="register-button" data-activity="${name}">Register</button>
        `;

        activitiesList.appendChild(card);
      });

      // Attach register button handlers
      document.querySelectorAll(".register-button").forEach((btn) => {
        btn.addEventListener("click", () => {
          hiddenActivityInput.value = btn.dataset.activity;
          modalActivityName.textContent = btn.dataset.activity;
          openModal(registrationModal);
        });
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // ---------------------------
  // Signup Form
  // ---------------------------
  signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const activity = hiddenActivityInput.value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}&teacher_username=${encodeURIComponent(teacherUsername || "")}`,
        { method: "POST" }
      );

      const result = await response.json();
      if (response.ok) {
        showMessage(result.message, "success");
        signupForm.reset();
        closeModal(registrationModal);
        fetchActivities();
      } else {
        showMessage(result.detail || "Error signing up", "error");
      }
    } catch (err) {
      showMessage("Failed to sign up.", "error");
      console.error(err);
    }
  });

  closeModalBtn.addEventListener("click", () => closeModal(registrationModal));

  // ---------------------------
  // Login / Logout
  // ---------------------------
  loginButton.addEventListener("click", () => openModal(loginModal));
  closeLoginModalBtn.addEventListener("click", () => closeModal(loginModal));

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const result = await response.json();
      if (response.ok) {
        teacherUsername = result.username;
        displayNameSpan.textContent = result.display_name;
        userInfo.classList.remove("hidden");
        loginButton.classList.add("hidden");
        closeModal(loginModal);
        loginMessage.classList.add("hidden");
      } else {
        loginMessage.textContent = result.detail || "Login failed";
        loginMessage.className = "message error";
        loginMessage.classList.remove("hidden");
      }
    } catch (err) {
      loginMessage.textContent = "Login error";
      loginMessage.className = "message error";
      loginMessage.classList.remove("hidden");
      console.error(err);
    }
  });

  logoutButton.addEventListener("click", () => {
    teacherUsername = null;
    userInfo.classList.add("hidden");
    loginButton.classList.remove("hidden");
    showMessage("Logged out", "success");
  });

  // ---------------------------
  // Filters & Search
  // ---------------------------
  categoryFilters.addEventListener("click", (e) => {
    if (e.target.classList.contains("category-filter")) {
      document.querySelectorAll(".category-filter").forEach((btn) =>
        btn.classList.remove("active")
      );
      e.target.classList.add("active");
      // For now, just reload activities (category filter logic can be added if categories are in DB)
      fetchActivities();
    }
  });

  dayFilters.addEventListener("click", (e) => {
    if (e.target.classList.contains("day-filter")) {
      document.querySelectorAll(".day-filter").forEach((btn) =>
        btn.classList.remove("active")
      );
      e.target.classList.add("active");
      const day = e.target.dataset.day;
      fetchActivities({ day });
    }
  });

  timeFilters.addEventListener("click", (e) => {
    if (e.target.classList.contains("time-filter")) {
      document.querySelectorAll(".time-filter").forEach((btn) =>
        btn.classList.remove("active")
      );
      e.target.classList.add("active");
      // Example: map time categories to start/end filters
      const time = e.target.dataset.time;
      let filters = {};
      if (time === "morning") filters.start_time = "07:00";
      if (time === "afternoon") filters.start_time = "14:00";
      if (time === "weekend") filters.day = "Saturday"; // simplistic example
      fetchActivities(filters);
    }
  });

  searchButton.addEventListener("click", () => {
    const term = searchBox.value.toLowerCase();
    document.querySelectorAll(".activity-card").forEach((card) => {
      const text = card.textContent.toLowerCase();
      card.style.display = text.includes(term) ? "" : "none";
    });
  });

  // ---------------------------
  // Initialize
  // ---------------------------
  fetchActivities();
});
