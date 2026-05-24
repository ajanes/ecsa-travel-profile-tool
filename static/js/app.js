(function () {
  const destination = window.APP_CONFIG.destination;
  const transportModes = window.APP_CONFIG.transportModes;
  const segmentsRoot = document.getElementById("segments");
  const addSegmentButton = document.getElementById("add-segment");
  const totalDistance = document.getElementById("total-distance");
  const totalEmissions = document.getElementById("total-emissions");
  const studyData = document.getElementById("study-data");
  const copyStudyDataButton = document.getElementById("copy-study-data");
  const copyStudyDataStatus = document.getElementById("copy-study-data-status");
  const transportModeCodes = Object.fromEntries(
    transportModes.map((mode, index) => [mode.key, index + 1]),
  );

  const state = {
    segments: [],
  };
  let pendingFocusSegmentId = null;

  function iconForMode(modeKey) {
    const map = {
      train: "train-front",
      bus_coach: "bus",
      car_diesel: "car-front",
      car_petrol: "car-front",
      car_electric: "car",
      car_plugin_hybrid: "car",
      motorbike: "bike",
      flight_domestic: "plane",
      flight_short_haul: "plane",
      flight_long_haul: "plane",
      ferry_foot: "ship",
      tram: "tram-front",
      metro: "tram-front",
    };
    return map[modeKey] || "move";
  }

  function createSegment() {
    return {
      id: crypto.randomUUID(),
      departure: null,
      departureQuery: "",
      arrival: null,
      arrivalQuery: "",
      transportMode: transportModes[0]?.key || "",
    };
  }

  function ensureMinimumSegments() {
    if (state.segments.length === 0) {
      state.segments.push(createSegment());
    }
  }

  function render() {
    ensureMinimumSegments();
    segmentsRoot.innerHTML = "";

    state.segments.forEach((segment, index) => {
      const isLast = index === state.segments.length - 1;
      if (isLast) {
        segment.arrival = destination;
        segment.arrivalQuery = destination.label;
      }

      const wrapper = document.createElement("article");
      wrapper.className = "segment";
      wrapper.innerHTML = `
        <div class="segment__header">
          <div>
            <p class="eyebrow">Segment ${index + 1}</p>
            <h3>${isLast ? "Final leg to conference" : "Travel leg"}</h3>
          </div>
          <div class="segment__controls">
            <button
              class="icon-button"
              type="button"
              data-remove="${segment.id}"
              aria-label="Remove segment"
              ${state.segments.length === 1 ? "disabled" : ""}
            >
              <i data-lucide="trash-2"></i>
            </button>
          </div>
        </div>
        <div class="segment__grid">
          ${placeFieldMarkup("Departure", "departure", segment)}
          ${isLast ? lockedArrivalMarkup() : placeFieldMarkup("Arrival", "arrival", segment)}
          <div class="field field--full">
            <label for="mode-${segment.id}">Transport mode</label>
            <div class="select-field">
              <select id="mode-${segment.id}" data-mode="${segment.id}">
                ${transportModes
                  .map(
                    (mode) => `
                      <option value="${mode.key}" ${mode.key === segment.transportMode ? "selected" : ""}>
                        ${mode.label}
                      </option>
                    `,
                  )
                  .join("")}
              </select>
              <span class="select-field__icon" aria-hidden="true">
                <i data-lucide="chevron-down"></i>
              </span>
            </div>
          </div>
        </div>
      `;

      segmentsRoot.appendChild(wrapper);
    });

    wireInteractions();
    lucide.createIcons();
    applyPendingFocus();
    recalculate();
  }

  function placeFieldMarkup(label, field, segment) {
    const value = field === "departure" ? segment.departureQuery : segment.arrivalQuery;
    return `
      <div class="field">
        <label for="${field}-${segment.id}">${label}</label>
        <input
          id="${field}-${segment.id}"
          name="${field}-${segment.id}"
          type="text"
          value="${escapeHtml(value || "")}"
          data-query="${segment.id}:${field}"
          autocomplete="off"
          placeholder="Search for a city, airport, or station"
        >
        <div class="suggestions hidden" data-suggestions="${segment.id}:${field}"></div>
      </div>
    `;
  }

  function lockedArrivalMarkup() {
    return `
      <div class="field">
        <label>Arrival</label>
        <div class="locked-destination">
          <i data-lucide="map-pinned"></i>
          <div>
            <strong>${destination.label}</strong>
          </div>
        </div>
      </div>
    `;
  }

  function wireInteractions() {
    segmentsRoot.querySelectorAll("[data-remove]").forEach((button) => {
      button.addEventListener("click", () => {
        const segmentId = button.dataset.remove;
        state.segments = state.segments.filter((segment) => segment.id !== segmentId);
        render();
      });
    });

    segmentsRoot.querySelectorAll("[data-mode]").forEach((select) => {
      select.addEventListener("change", () => {
        const segment = state.segments.find((item) => item.id === select.dataset.mode);
        segment.transportMode = select.value;
        recalculate();
      });
    });

    segmentsRoot.querySelectorAll("[data-query]").forEach((input) => {
      input.addEventListener(
        "input",
        debounce(async () => {
          const [segmentId, field] = input.dataset.query.split(":");
          const segment = state.segments.find((item) => item.id === segmentId);
          segment[`${field}Query`] = input.value;
          segment[field] = null;
          renderSuggestions(input, await searchPlaces(input.value), segmentId, field);
          recalculate();
        }, 250),
      );
    });
  }

  function renderSuggestions(input, suggestions, segmentId, field) {
    const container = document.querySelector(`[data-suggestions="${segmentId}:${field}"]`);
    if (!container) return;

    if (suggestions.length === 0) {
      container.classList.add("hidden");
      container.innerHTML = "";
      return;
    }

    container.innerHTML = suggestions
      .map(
        (item) => `
          <button class="suggestion" type="button" data-place="${encodeURIComponent(JSON.stringify(item))}">
            ${escapeHtml(item.label)}
            <small>${escapeHtml(item.type)}${item.country ? ` · ${escapeHtml(item.country)}` : ""}</small>
          </button>
        `,
      )
      .join("");
    container.classList.remove("hidden");

    container.querySelectorAll("[data-place]").forEach((button) => {
      button.addEventListener("click", () => {
        const place = JSON.parse(decodeURIComponent(button.dataset.place));
        const segmentIndex = state.segments.findIndex((item) => item.id === segmentId);
        const segment = state.segments[segmentIndex];
        segment[field] = place;
        segment[`${field}Query`] = place.label;

        if (field === "arrival") {
          const nextSegment = state.segments[segmentIndex + 1];
          if (nextSegment) {
            nextSegment.departure = place;
            nextSegment.departureQuery = place.label;
          }
        }

        render();
      });
    });
  }

  async function searchPlaces(query) {
    if (!query || query.trim().length < 2) {
      return [];
    }

    const response = await fetch(`/api/places?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
      return [];
    }

    const data = await response.json();
    return data.results || [];
  }

  async function recalculate() {
    const payload = {
      segments: state.segments.map((segment, index) => ({
        departure: segment.departure,
        arrival: index === state.segments.length - 1 ? destination : segment.arrival,
        transport_mode: segment.transportMode,
      })),
    };

    const completeSegments = payload.segments.filter(
      (segment) => segment.departure && segment.arrival && segment.transport_mode,
    );

    if (completeSegments.length !== payload.segments.length) {
      showEmptyState();
      return;
    }

    const response = await fetch("/api/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      showEmptyState();
      return;
    }

    const result = await response.json();
    renderResults(result, payload);
  }

  function renderResults(result, payload) {
    totalDistance.textContent = `${result.total_distance_km} km`;
    totalEmissions.textContent = `${result.total_emissions_kg} kg CO2e`;
    studyData.value = buildStudyDataString(payload);
    lucide.createIcons();
  }

  function showEmptyState() {
    totalDistance.textContent = "0 km";
    totalEmissions.textContent = "0 kg CO2e";
    studyData.value = "";
    copyStudyDataStatus.textContent = "";
  }

  function buildStudyDataString(payload) {
    return payload.segments
      .map(
        (segment) =>
          [
            roundCoordinate(segment.departure.lat),
            roundCoordinate(segment.departure.lon),
            transportModeCodes[segment.transport_mode] || 0,
            roundCoordinate(segment.arrival.lat),
            roundCoordinate(segment.arrival.lon),
          ].join(","),
      )
      .join(";");
  }

  function roundCoordinate(value) {
    return Math.round(Number(value) * 10000) / 10000;
  }

  function applyPendingFocus() {
    if (!pendingFocusSegmentId) {
      return;
    }

    const input = document.getElementById(`departure-${pendingFocusSegmentId}`);
    if (input) {
      input.focus();
      pendingFocusSegmentId = null;
    }
  }

  function debounce(fn, wait) {
    let timeoutId;
    return (...args) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn(...args), wait);
    };
  }

  function escapeHtml(value) {
    return value
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  async function copyStudyData() {
    if (!studyData.value) {
      copyStudyDataStatus.textContent = "Nothing to copy yet.";
      return;
    }

    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(studyData.value);
      } else {
        studyData.focus();
        studyData.select();
        studyData.setSelectionRange(0, studyData.value.length);
        if (!document.execCommand("copy")) {
          throw new Error("Copy command failed");
        }
      }

      copyStudyDataStatus.textContent = "Copied.";
    } catch (error) {
      copyStudyDataStatus.textContent = "Copy failed. Select the text and copy it manually.";
    }
  }

  addSegmentButton.addEventListener("click", () => {
    const currentLastSegment = state.segments[state.segments.length - 1];
    if (currentLastSegment) {
      currentLastSegment.arrival = null;
      currentLastSegment.arrivalQuery = "";
    }

    const newSegment = createSegment();
    pendingFocusSegmentId = newSegment.id;
    state.segments.push(newSegment);
    render();
  });

  copyStudyDataButton.addEventListener("click", () => {
    copyStudyData();
  });

  render();
})();
