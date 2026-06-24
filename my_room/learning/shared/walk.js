/* shared progress + navigation for walks
   markers, not checkmarks — re-reading is the default */

(function () {
  const NS = "tos.walk";

  function key(topic, walk, k) { return `${NS}.${topic}.${walk}.${k}`; }

  window.Walk = {
    /* call this once at the bottom of each walk html */
    init({ topic, walk, totalSteps, onStep }) {
      const state = {
        topic, walk, totalSteps,
        current: 0,
        visited: new Set(),
      };

      // restore last step if there is one
      const lastStep = parseInt(localStorage.getItem(key(topic, walk, "last-step")) || "0", 10);
      const visitedRaw = localStorage.getItem(key(topic, walk, "visited-steps")) || "[]";
      try { JSON.parse(visitedRaw).forEach(s => state.visited.add(s)); } catch (e) {}

      // record this visit timestamp + bump visits count
      localStorage.setItem(key(topic, walk, "last-visit"), new Date().toISOString());
      const visits = parseInt(localStorage.getItem(key(topic, walk, "visits")) || "0", 10);
      localStorage.setItem(key(topic, walk, "visits"), String(visits + 1));

      // offer to resume — only if mid-walk
      if (lastStep > 0 && lastStep < totalSteps - 1) {
        // small async so the page can render the first step in the meantime
        setTimeout(() => {
          const resume = confirm(
            `you left off at step ${lastStep + 1} of ${totalSteps}. pick up there?\n\n` +
            `ok = resume at ${lastStep + 1}\ncancel = start fresh from step 1`
          );
          if (resume) goTo(lastStep);
        }, 200);
      }

      function goTo(idx) {
        if (idx < 0 || idx >= totalSteps) return;
        state.current = idx;
        state.visited.add(idx);
        localStorage.setItem(key(topic, walk, "last-step"), String(idx));
        localStorage.setItem(key(topic, walk, "visited-steps"), JSON.stringify([...state.visited]));
        renderDots();
        onStep(idx, { totalSteps, isFirst: idx === 0, isLast: idx === totalSteps - 1 });
        window.scrollTo({ top: 0, behavior: "smooth" });
      }

      function renderDots() {
        const dots = document.querySelectorAll(".walk-dot");
        dots.forEach((d, i) => {
          let state2 = "future";
          if (i === state.current) state2 = "current";
          else if (state.visited.has(i)) state2 = "visited";
          d.dataset.state = state2;
        });
      }

      // build the dot row
      const dotsContainer = document.querySelector(".walk-progress");
      if (dotsContainer) {
        dotsContainer.innerHTML = "";
        for (let i = 0; i < totalSteps; i++) {
          const b = document.createElement("button");
          b.className = "walk-dot";
          b.setAttribute("aria-label", `go to step ${i + 1}`);
          b.addEventListener("click", () => goTo(i));
          dotsContainer.appendChild(b);
        }
      }

      // public api
      state.goTo = goTo;
      state.next = () => goTo(state.current + 1);
      state.prev = () => goTo(state.current - 1);
      state.markComplete = () => {
        localStorage.setItem(key(topic, walk, "completed-at"), new Date().toISOString());
      };

      // initial render
      goTo(0);

      return state;
    },

    /* helpers for the index pages */
    getMarker(topic, walk) {
      const visit = localStorage.getItem(key(topic, walk, "last-visit"));
      const visits = parseInt(localStorage.getItem(key(topic, walk, "visits")) || "0", 10);
      const completed = localStorage.getItem(key(topic, walk, "completed-at"));
      return { lastVisit: visit, visits, completed };
    },

    formatMarker(marker) {
      if (!marker.lastVisit) return null;
      const d = new Date(marker.lastVisit);
      const now = new Date();
      const sameDay = d.toDateString() === now.toDateString();
      const yesterday = new Date(now);
      yesterday.setDate(now.getDate() - 1);
      const wasYesterday = d.toDateString() === yesterday.toDateString();
      const dayDiff = Math.floor((now - d) / (1000 * 60 * 60 * 24));

      let when;
      if (sameDay) when = "you came here today";
      else if (wasYesterday) when = "you came here yesterday";
      else if (dayDiff < 7) when = `you came here ${dayDiff} days ago`;
      else {
        when = `you came here on ${d.toLocaleDateString("en-US", { month: "short", day: "numeric" }).toLowerCase()}`;
      }
      if (marker.visits > 1) when += ` · ${marker.visits} visits`;
      return when;
    },
  };
})();
