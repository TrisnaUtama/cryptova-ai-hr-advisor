// Tab button functionality
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", function () {
    document.querySelectorAll(".tab-btn").forEach((b) => {
      b.classList.remove("active", "bg-white", "shadow-md");
      b.classList.add("bg-gray-100", "text-gray-700");
    });
    this.classList.add("active", "bg-white", "shadow-md");
    this.classList.remove("bg-gray-100", "text-gray-700");
    // Tab content
    document
      .querySelectorAll(".tab-content")
      .forEach((tc) => tc.classList.remove("active"));
    document.getElementById("tab-" + this.dataset.tab).classList.add("active");
  });
});

// Overview tab
if (
  document.getElementById("tab-overview") &&
  document.getElementById("tab-overview").classList.contains("active")
) {
  // CV processing chart
  new Chart(document.getElementById("cvProcessingChart"), {
    type: "line",
    data: {
      labels: window.week_labels || [],
      datasets: [
        {
          label: "Uploaded",
          data: window.uploaded_cvs,
          borderColor: "#2563eb",
          backgroundColor: "rgba(37,99,235,0.1)",
          tension: 0.4,
        },
        {
          label: "Processed",
          data: window.processed_cvs,
          borderColor: "#fbbf24",
          backgroundColor: "rgba(251,191,36,0.1)",
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true } },
      scales: { y: { beginAtZero: true } },
    },
  });

  // Average score chart
  const avgScores = window.avg_scores || [];
  let minY = 60;
  let maxY = 100;
  if (avgScores.length > 0) {
    minY = Math.floor(Math.min(...avgScores));
    maxY = Math.ceil(Math.max(...avgScores));
    minY = Math.max(minY - 5, 0);
    maxY = Math.min(maxY + 5, 100);
    if (minY === maxY) {
      minY = minY - 5;
      maxY = maxY + 5;
    }
  }
  new Chart(document.getElementById("avgScoreChart"), {
    type: "line",
    data: {
      labels: window.week_labels || [],
      datasets: [
        {
          label: "Score",
          data: avgScores,
          borderColor: "#2563eb",
          backgroundColor: "rgba(37,99,235,0.1)",
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { min: minY, max: maxY } },
    },
  });

  // CVs processing report by day chart
  new Chart(document.getElementById("cvByDayChart"), {
    type: "bar",
    data: {
      labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      datasets: [
        {
          label: "Uploads",
          data: window.uploaded_cvs_per_day,
          backgroundColor: "#2563eb",
        },
        {
          label: "Parsed",
          data: window.parsed_cvs_per_day,
          backgroundColor: "#fbbf24",
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true } },
      scales: { y: { beginAtZero: true } },
    },
  });
}

// Slider value update
const sliders = [
  { id: "expWeight", val: "expWeightVal" },
  { id: "skillsWeight", val: "skillsWeightVal" },
  { id: "achievementsWeight", val: "achievementsWeightVal" },
  { id: "certificatesWeight", val: "certificatesWeightVal" },
  { id: "gpaWeight", val: "gpaWeightVal" },
];
function updateTotal() {
  let total = 0;
  sliders.forEach((s) => {
    total += parseInt(document.getElementById(s.id).value);
  });
  document.getElementById("totalWeight").innerText = total;
}
sliders.forEach((s) => {
  const slider = document.getElementById(s.id);
  const val = document.getElementById(s.val);
  slider.addEventListener("input", function () {
    val.innerText = this.value;
    updateTotal();
  });
});
updateTotal();

// Score Distribution Chart
function renderScoreDistChart() {
  if (window.scoreDistChartInstance) {
    window.scoreDistChartInstance.destroy();
  }
  const ctx = document.getElementById("scoreDistChart");
  if (!ctx) return;
  window.scoreDistChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["0-20", "21-40", "41-60", "61-80", "81-100"],
      datasets: [
        {
          label: "Candidates",
          data: window.score_distribution,
          backgroundColor: "#1e3a8a",
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } },
    },
  });
}
renderScoreDistChart();
