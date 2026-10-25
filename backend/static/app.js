const API = "/api/v1";

const state = {
  teacher: null,
  token: localStorage.getItem("mektep_token") || "",
};

function $(sel, root = document) {
  return root.querySelector(sel);
}

function html(strings, ...values) {
  return strings.reduce((acc, s, i) => acc + s + (values[i] ?? ""), "");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData) && options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const res = await fetch(API + path, { ...options, headers });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text };
  }
  if (!res.ok) {
    const detail = data && data.detail;
    const msg = Array.isArray(detail) ? detail.map((d) => d.msg).join(", ") : detail || "Қате";
    throw new Error(msg);
  }
  return data;
}

function go(path) {
  history.pushState({}, "", path);
  render();
}

window.addEventListener("popstate", render);

function topPublic() {
  return html`
    <div class="wrap topbar">
      <a class="brand" href="/"><span class="mark">M</span> Mektep AI</a>
      <div class="nav">
        <a class="btn secondary" href="/join">Оқушыға тест</a>
        <a class="btn" href="/login">Мұғалім кіру</a>
      </div>
    </div>
  `;
}

function layoutTeacher(active, body) {
  const t = state.teacher;
  return html`
    <div class="layout">
      <aside class="side">
        <a class="brand" href="/app" style="margin-bottom:18px">
          <span class="mark">M</span> Mektep AI
        </a>
        <div class="muted" style="color:#b7d4d1;padding:0 12px 12px">${escapeHtml(t?.full_name || "")}</div>
        <a class="${active === "dash" ? "active" : ""}" href="/app">Басты бет</a>
        <a class="${active === "materials" ? "active" : ""}" href="/app/materials">Жоспар / силлабус</a>
        <a class="${active === "tests" ? "active" : ""}" href="/app/tests">Тесттер</a>
        <a href="/" id="logout">Шығу</a>
      </aside>
      <div class="main">${body}</div>
    </div>
  `;
}

function emptyQuestion(qtype = "closed") {
  return {
    qtype,
    prompt: "",
    options: ["", "", "", ""],
    correct_option: 0,
    reference_answer: "",
    topic: "",
    max_score: 1,
  };
}

async function viewHome() {
  document.getElementById("app").innerHTML = html`
    ${topPublic()}
    <div class="wrap hero">
      <div>
        <p class="chip">Қазақстан мектептеріне</p>
        <h1>Сабақ жоспары, тест және AI талдау — бір жерде.</h1>
        <p class="lede">
          Мұғалім кіреді, силлабус пен жоспар жүктейді, жабық және ашық сұрақтары бар тест құрады.
          Оқушы тіркелмейді: атын жазып, тестті өтеді. Ашық жауаптарды Gemini қазақша талдайды:
          не қате, неліктен, қайдан бастау және нені оқу керек.
        </p>
        <div class="row" style="margin-top:22px">
          <a class="btn" href="/register">Мұғалім тіркелу</a>
          <a class="btn secondary" href="/join">Тест кодымен кіру</a>
        </div>
      </div>
      <div class="panel">
        <h3>Оқушыға</h3>
        <label>Тест коды</label>
        <input id="home-code" placeholder="мысалы, 7K2Q9P" />
        <label>Аты-жөні</label>
        <input id="home-name" placeholder="Айша Нұрланова" />
        <label>Сынып (міндетті емес)</label>
        <input id="home-class" placeholder="8А" />
        <p class="err" id="home-err"></p>
        <button class="btn" id="home-start" style="margin-top:14px;width:100%">Тестті бастау</button>
      </div>
    </div>
    <div class="wrap cards">
      <div class="panel card">
        <h3>1. Мұғалім</h3>
        <p>Жоспар, силлабус және тест банкі.</p>
      </div>
      <div class="panel card">
        <h3>2. Оқушы</h3>
        <p>Аты мен код. Аккаунт керек емес.</p>
      </div>
      <div class="panel card">
        <h3>3. Gemini</h3>
        <p>Ашық жауапқа қазақша кері байланыс.</p>
      </div>
    </div>
  `;
  $("#home-start").onclick = async () => {
    $("#home-err").textContent = "";
    try {
      const code = $("#home-code").value.trim();
      const started = await api(`/public/tests/${encodeURIComponent(code)}/start`, {
        method: "POST",
        body: JSON.stringify({
          student_name: $("#home-name").value.trim(),
          class_name: $("#home-class").value.trim(),
        }),
      });
      sessionStorage.setItem("attempt", JSON.stringify(started));
      go(`/take/${started.attempt_id}`);
    } catch (e) {
      $("#home-err").textContent = e.message;
    }
  };
}

function authForm(mode) {
  const title = mode === "login" ? "Мұғалім кіру" : "Мұғалім тіркелу";
  return html`
    ${topPublic()}
    <div class="wrap" style="max-width:480px;padding:20px 0 60px">
      <div class="panel">
        <h2>${title}</h2>
        ${
          mode === "register"
            ? `<label>Аты-жөні</label><input id="full_name" />
               <label>Мектеп</label><input id="school_name" />`
            : ""
        }
        <label>Email</label>
        <input id="email" type="email" />
        <label>Құпиясөз</label>
        <input id="password" type="password" />
        <p class="err" id="auth-err"></p>
        <button class="btn" id="auth-go" style="margin-top:14px;width:100%">${title}</button>
        <p class="muted">${
          mode === "login"
            ? `Аккаунт жоқ па? <a href="/register">Тіркелу</a>`
            : `Аккаунт бар ма? <a href="/login">Кіру</a>`
        }</p>
      </div>
    </div>
  `;
}

async function viewAuth(mode) {
  document.getElementById("app").innerHTML = authForm(mode);
  $("#auth-go").onclick = async () => {
    $("#auth-err").textContent = "";
    try {
      const payload = {
        email: $("#email").value,
        password: $("#password").value,
      };
      if (mode === "register") {
        payload.full_name = $("#full_name").value;
        payload.school_name = $("#school_name").value;
      }
      const data = await api(mode === "login" ? "/auth/login" : "/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      state.token = data.access_token;
      state.teacher = data.teacher;
      localStorage.setItem("mektep_token", state.token);
      go("/app");
    } catch (e) {
      $("#auth-err").textContent = e.message;
    }
  };
}

async function requireTeacher() {
  if (!state.token) {
    go("/login");
    return null;
  }
  if (!state.teacher) {
    try {
      state.teacher = await api("/auth/me");
    } catch {
      state.token = "";
      localStorage.removeItem("mektep_token");
      go("/login");
      return null;
    }
  }
  return state.teacher;
}

async function viewDash() {
  if (!(await requireTeacher())) return;
  const tests = await api("/tests");
  const materials = await api("/materials");
  document.getElementById("app").innerHTML = layoutTeacher(
    "dash",
    html`
      <h1>Сәлеметсіз бе, ${escapeHtml(state.teacher.full_name)}</h1>
      <p class="muted">${escapeHtml(state.teacher.school_name || "Мектеп көрсетілмеген")}</p>
      <div class="cards">
        <div class="panel card"><h3>${tests.length}</h3><p>тест</p></div>
        <div class="panel card"><h3>${materials.length}</h3><p>жүктелген құжат</p></div>
        <div class="panel card"><h3>${tests.reduce((s, t) => s + t.attempt_count, 0)}</h3><p>оқушы әрекеті</p></div>
      </div>
      <div class="row">
        <a class="btn" href="/app/tests/new">Жаңа тест</a>
        <a class="btn secondary" href="/app/materials">Құжат жүктеу</a>
      </div>
    `
  );
}

async function viewMaterials() {
  if (!(await requireTeacher())) return;
  const items = await api("/materials");
  const rows = items
    .map(
      (m) => html`
        <tr>
          <td>${m.kind === "syllabus" ? "Силлабус" : "Оқу жоспары"}</td>
          <td>${escapeHtml(m.title)}</td>
          <td>${escapeHtml(m.original_name)}</td>
          <td>
            <a href="${API}/materials/${m.id}/download" data-dl="${m.id}">Жүктеу</a>
            · <a href="#" data-del="${m.id}">Өшіру</a>
          </td>
        </tr>
      `
    )
    .join("");
  document.getElementById("app").innerHTML = layoutTeacher(
    "materials",
    html`
      <h1>Оқу жоспары және силлабус</h1>
      <div class="grid-2">
        <div class="panel">
          <h3>Жаңа файл</h3>
          <label>Түрі</label>
          <select id="kind">
            <option value="study_plan">Оқу жоспары</option>
            <option value="syllabus">Силлабус</option>
          </select>
          <label>Атауы</label>
          <input id="title" placeholder="8-сынып Қазақ әдебиеті" />
          <label>Файл (PDF, DOC, DOCX)</label>
          <input id="file" type="file" />
          <p class="err" id="mat-err"></p>
          <button class="btn" id="mat-up" style="margin-top:12px">Жүктеу</button>
        </div>
        <div class="panel">
          <p class="muted">Бұл құжаттар мұғалімнің мұрағаты. Кейін AI ұсыныстарын солармен байланыстыруға болады.</p>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <table class="table">
          <thead><tr><th>Түрі</th><th>Атауы</th><th>Файл</th><th></th></tr></thead>
          <tbody>${rows || `<tr><td colspan="4" class="muted">Әлі файл жоқ</td></tr>`}</tbody>
        </table>
      </div>
    `
  );
  $("#mat-up").onclick = async () => {
    $("#mat-err").textContent = "";
    const file = $("#file").files[0];
    if (!file) {
      $("#mat-err").textContent = "Файл таңдаңыз";
      return;
    }
    const fd = new FormData();
    fd.append("kind", $("#kind").value);
    fd.append("title", $("#title").value);
    fd.append("file", file);
    try {
      await api("/materials", { method: "POST", body: fd });
      viewMaterials();
    } catch (e) {
      $("#mat-err").textContent = e.message;
    }
  };
  document.querySelectorAll("[data-del]").forEach((el) => {
    el.onclick = async (ev) => {
      ev.preventDefault();
      await api(`/materials/${el.dataset.del}`, { method: "DELETE" });
      viewMaterials();
    };
  });
  document.querySelectorAll("[data-dl]").forEach((el) => {
    el.onclick = async (ev) => {
      ev.preventDefault();
      const res = await fetch(API + `/materials/${el.dataset.dl}/download`, {
        headers: { Authorization: `Bearer ${state.token}` },
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "material";
      a.click();
    };
  });
}

function questionEditor(q, idx) {
  const options = (q.options || ["", "", "", ""]).map(
    (opt, i) => html`
      <div class="row" style="margin:6px 0">
        <input data-opt="${idx}:${i}" value="${escapeHtml(opt)}" placeholder="Нұсқа ${i + 1}" />
        <label style="margin:0;display:flex;align-items:center;gap:6px;white-space:nowrap">
          <input type="radio" name="correct-${idx}" value="${i}" ${Number(q.correct_option) === i ? "checked" : ""} />
          дұрыс
        </label>
      </div>
    `
  );
  return html`
    <div class="qbox" data-q="${idx}">
      <div class="row">
        <strong>Сұрақ ${idx + 1}</strong>
        <select data-type="${idx}">
          <option value="closed" ${q.qtype === "closed" ? "selected" : ""}>Жабық</option>
          <option value="open" ${q.qtype === "open" ? "selected" : ""}>Ашық</option>
        </select>
        <button class="btn secondary" data-rm="${idx}" type="button">Өшіру</button>
      </div>
      <label>Мәтін</label>
      <textarea data-prompt="${idx}">${escapeHtml(q.prompt)}</textarea>
      <label>Тақырып</label>
      <input data-topic="${idx}" value="${escapeHtml(q.topic || "")}" placeholder="Мысалы: Абайдың қара сөздері" />
      <div class="closed-block" style="${q.qtype === "open" ? "display:none" : ""}">
        <label>Нұсқалар</label>
        ${options.join("")}
      </div>
      <div class="open-block" style="${q.qtype === "closed" ? "display:none" : ""}">
        <label>Үлгі жауап (AI үшін, оқушыға көрсетілмейді)</label>
        <textarea data-ref="${idx}">${escapeHtml(q.reference_answer || "")}</textarea>
      </div>
    </div>
  `;
}

function collectQuestions() {
  return [...document.querySelectorAll(".qbox")].map((box, idx) => {
    const qtype = box.querySelector("[data-type]").value;
    const options = [...box.querySelectorAll("[data-opt]")].map((i) => i.value);
    const checked = box.querySelector(`input[name="correct-${idx}"]:checked`);
    return {
      qtype,
      prompt: box.querySelector("[data-prompt]").value,
      options,
      correct_option: checked ? Number(checked.value) : 0,
      reference_answer: box.querySelector("[data-ref]")?.value || "",
      topic: box.querySelector("[data-topic]").value,
      max_score: 1,
      position: idx,
    };
  });
}

function bindQuestionEditor() {
  document.querySelectorAll("[data-type]").forEach((sel) => {
    sel.onchange = () => {
      const box = sel.closest(".qbox");
      box.querySelector(".closed-block").style.display = sel.value === "closed" ? "" : "none";
      box.querySelector(".open-block").style.display = sel.value === "open" ? "" : "none";
    };
  });
}

async function viewTests() {
  if (!(await requireTeacher())) return;
  const tests = await api("/tests");
  const rows = tests
    .map(
      (t) => html`
        <tr>
          <td><a href="/app/tests/${t.id}">${escapeHtml(t.title)}</a></td>
          <td>${escapeHtml(t.subject)} / ${escapeHtml(t.grade)}</td>
          <td><code>${t.public_code}</code></td>
          <td>${t.question_count}</td>
          <td><a href="/app/tests/${t.id}/results">${t.attempt_count} нәтиже</a></td>
        </tr>
      `
    )
    .join("");
  document.getElementById("app").innerHTML = layoutTeacher(
    "tests",
    html`
      <div class="row" style="justify-content:space-between">
        <h1>Тесттер</h1>
        <a class="btn" href="/app/tests/new">Жаңа тест</a>
      </div>
      <div class="panel">
        <table class="table">
          <thead><tr><th>Атауы</th><th>Пән</th><th>Код</th><th>Сұрақ</th><th>Нәтиже</th></tr></thead>
          <tbody>${rows || `<tr><td colspan="5" class="muted">Тест жоқ</td></tr>`}</tbody>
        </table>
      </div>
    `
  );
}

async function viewTestEditor(id) {
  if (!(await requireTeacher())) return;
  let test = {
    title: "",
    subject: "",
    grade: "",
    description: "",
    time_limit_minutes: 0,
    questions: [emptyQuestion("closed"), emptyQuestion("open")],
  };
  if (id !== "new") test = await api(`/tests/${id}`);
  const qhtml = (test.questions.length ? test.questions : [emptyQuestion()]).map(questionEditor).join("");
  document.getElementById("app").innerHTML = layoutTeacher(
    "tests",
    html`
      <h1>${id === "new" ? "Жаңа тест" : "Тестті өңдеу"}</h1>
      <div class="panel">
        <div class="grid-2">
          <div>
            <label>Атауы</label>
            <input id="title" value="${escapeHtml(test.title)}" />
          </div>
          <div>
            <label>Пән</label>
            <input id="subject" value="${escapeHtml(test.subject || "")}" />
          </div>
          <div>
            <label>Сынып</label>
            <input id="grade" value="${escapeHtml(test.grade || "")}" />
          </div>
          <div>
            <label>Уақыт (минут, 0 = шексіз)</label>
            <input id="time" type="number" value="${test.time_limit_minutes || 0}" />
          </div>
        </div>
        <label>Сипаттама</label>
        <textarea id="desc">${escapeHtml(test.description || "")}</textarea>
        ${id !== "new" ? `<p>Оқушы коды: <code>${test.public_code}</code> — сілтеме: <code>/t/${test.public_code}</code></p>` : ""}
        <div id="qs">${qhtml}</div>
        <div class="row">
          <button class="btn secondary" id="add-closed" type="button">+ Жабық сұрақ</button>
          <button class="btn secondary" id="add-open" type="button">+ Ашық сұрақ</button>
        </div>
        <p class="err" id="save-err"></p>
        <button class="btn" id="save" style="margin-top:16px">Сақтау</button>
        ${id !== "new" ? `<button class="btn danger" id="del" style="margin-left:8px">Тестті өшіру</button>` : ""}
      </div>
    `
  );
  bindQuestionEditor();
  const refreshQs = () => {
    const current = collectQuestions();
    $("#qs").innerHTML = current.map(questionEditor).join("");
    bindQuestionEditor();
    document.querySelectorAll("[data-rm]").forEach((b) => {
      b.onclick = () => {
        b.closest(".qbox").remove();
        refreshQs();
      };
    });
  };
  document.querySelectorAll("[data-rm]").forEach((b) => {
    b.onclick = () => {
      b.closest(".qbox").remove();
      refreshQs();
    };
  });
  $("#add-closed").onclick = () => {
    const qs = collectQuestions();
    qs.push(emptyQuestion("closed"));
    $("#qs").innerHTML = qs.map(questionEditor).join("");
    bindQuestionEditor();
    refreshQs();
  };
  $("#add-open").onclick = () => {
    const qs = collectQuestions();
    qs.push(emptyQuestion("open"));
    $("#qs").innerHTML = qs.map(questionEditor).join("");
    bindQuestionEditor();
    refreshQs();
  };
  $("#save").onclick = async () => {
    $("#save-err").textContent = "";
    const payload = {
      title: $("#title").value,
      subject: $("#subject").value,
      grade: $("#grade").value,
      description: $("#desc").value,
      time_limit_minutes: Number($("#time").value || 0),
      is_published: true,
      questions: collectQuestions(),
    };
    try {
      const saved =
        id === "new"
          ? await api("/tests", { method: "POST", body: JSON.stringify(payload) })
          : await api(`/tests/${id}`, { method: "PUT", body: JSON.stringify(payload) });
      go(`/app/tests/${saved.id}`);
    } catch (e) {
      $("#save-err").textContent = e.message;
    }
  };
  const del = $("#del");
  if (del) {
    del.onclick = async () => {
      if (!confirm("Тестті өшіресіз бе?")) return;
      await api(`/tests/${id}`, { method: "DELETE" });
      go("/app/tests");
    };
  }
}

async function viewResults(testId) {
  if (!(await requireTeacher())) return;
  const test = await api(`/tests/${testId}`);
  const attempts = await api(`/tests/${testId}/attempts`);
  const rows = attempts
    .map((a) => {
      const total = a.closed_score + a.open_score;
      const max = a.closed_max + a.open_max;
      return html`
        <tr>
          <td><a href="/app/attempts/${a.id}">${escapeHtml(a.student_name)}</a></td>
          <td>${escapeHtml(a.class_name)}</td>
          <td>${a.status}</td>
          <td>${total.toFixed(1)} / ${max.toFixed(1)}</td>
        </tr>
      `;
    })
    .join("");
  document.getElementById("app").innerHTML = layoutTeacher(
    "tests",
    html`
      <h1>${escapeHtml(test.title)} — нәтижелер</h1>
      <p>Код: <code>${test.public_code}</code></p>
      <div class="panel">
        <table class="table">
          <thead><tr><th>Оқушы</th><th>Сынып</th><th>Күй</th><th>Ұпай</th></tr></thead>
          <tbody>${rows || `<tr><td colspan="4" class="muted">Әлі ешкім өтпеген</td></tr>`}</tbody>
        </table>
      </div>
    `
  );
}

function renderAttempt(attempt, backHref) {
  const answers = attempt.answers
    .map((a, i) => {
      const fb = a.feedback || {};
      const study = (fb.what_to_study || []).map((t) => `<span class="chip">${escapeHtml(t)}</span>`).join(" ");
      const closed = a.qtype === "closed";
      return html`
        <div class="qbox">
          <div class="row"><strong>${i + 1}.</strong> <span class="chip">${closed ? "жабық" : "ашық"}</span>
            <span class="${a.is_correct ? "ok" : "err"}">${a.score} / ${a.max_score}</span></div>
          <p>${escapeHtml(a.prompt)}</p>
          <p><b>Жауап:</b> ${escapeHtml(closed ? `нұсқа ${a.selected_option + 1}` : a.text_answer || "—")}</p>
          ${
            !closed
              ? html`
                  <div class="feedback">
                    <p><b>Не қате:</b> ${escapeHtml(fb.what_is_wrong || "—")}</p>
                    <p><b>Неліктен:</b> ${escapeHtml(fb.why_wrong || "—")}</p>
                    <p><b>Қайдан бастау:</b> ${escapeHtml(fb.where_to_start || "—")}</p>
                    <p><b>Не оқу керек:</b> ${study || "—"}</p>
                    <p><b>Бағыт:</b> ${escapeHtml(fb.correct_direction || "—")}</p>
                  </div>
                `
              : ""
          }
        </div>
      `;
    })
    .join("");
  const total = attempt.closed_score + attempt.open_score;
  const max = attempt.closed_max + attempt.open_max;
  return html`
    <div class="wrap" style="padding:20px 0 60px">
      <a href="${backHref}">← артқа</a>
      <h1>${escapeHtml(attempt.test_title)}</h1>
      <p>${escapeHtml(attempt.student_name)} · ${escapeHtml(attempt.class_name)}</p>
      <div class="panel">
        <p>Жабық: ${attempt.closed_score}/${attempt.closed_max} · Ашық: ${attempt.open_score}/${attempt.open_max} · Барлығы: <b>${total.toFixed(1)} / ${max.toFixed(1)}</b></p>
        ${answers}
      </div>
    </div>
  `;
}

async function viewTeacherAttempt(id) {
  if (!(await requireTeacher())) return;
  const attempt = await api(`/attempts/${id}`);
  document.getElementById("app").innerHTML = layoutTeacher("tests", renderAttempt(attempt, `/app/tests/${attempt.test_id}/results`));
}

async function viewJoin() {
  document.getElementById("app").innerHTML = html`
    ${topPublic()}
    <div class="wrap" style="max-width:480px;padding:20px 0">
      <div class="panel">
        <h2>Тестке кіру</h2>
        <label>Код</label><input id="code" />
        <label>Аты-жөні</label><input id="name" />
        <label>Сынып</label><input id="klass" />
        <p class="err" id="err"></p>
        <button class="btn" id="go" style="margin-top:12px;width:100%">Бастау</button>
      </div>
    </div>
  `;
  $("#go").onclick = async () => {
    try {
      const started = await api(`/public/tests/${encodeURIComponent($("#code").value.trim())}/start`, {
        method: "POST",
        body: JSON.stringify({ student_name: $("#name").value.trim(), class_name: $("#klass").value.trim() }),
      });
      sessionStorage.setItem("attempt", JSON.stringify(started));
      go(`/take/${started.attempt_id}`);
    } catch (e) {
      $("#err").textContent = e.message;
    }
  };
}

async function viewTake(attemptId) {
  const cached = JSON.parse(sessionStorage.getItem("attempt") || "null");
  let test = cached && cached.attempt_id === attemptId ? cached.test : null;
  if (!test) {
    document.getElementById("app").innerHTML = html`${topPublic()}<div class="wrap"><p>Сессия жоқ. Кодпен қайта кіріңіз.</p></div>`;
    return;
  }
  const qs = test.questions
    .map((q, i) => {
      if (q.qtype === "closed") {
        const opts = (q.options || [])
          .map(
            (o, idx) =>
              `<label><input type="radio" name="q-${q.id}" value="${idx}" /> ${escapeHtml(o)}</label>`
          )
          .join("");
        return `<div class="qbox"><p><b>${i + 1}.</b> ${escapeHtml(q.prompt)}</p><div class="options">${opts}</div></div>`;
      }
      return `<div class="qbox"><p><b>${i + 1}.</b> ${escapeHtml(q.prompt)}</p><textarea id="t-${q.id}" placeholder="Жауабыңызды жазыңыз"></textarea></div>`;
    })
    .join("");
  document.getElementById("app").innerHTML = html`
    ${topPublic()}
    <div class="wrap" style="padding-bottom:50px">
      <h1>${escapeHtml(test.title)}</h1>
      <p class="muted">${escapeHtml(test.subject)} · ${escapeHtml(test.grade)}</p>
      ${qs}
      <p class="err" id="err"></p>
      <button class="btn" id="submit">Тапсыру</button>
    </div>
  `;
  $("#submit").onclick = async () => {
    $("#err").textContent = "";
    $("#submit").disabled = true;
    $("#submit").textContent = "Талданып жатыр…";
    const answers = test.questions.map((q) => {
      if (q.qtype === "closed") {
        const checked = document.querySelector(`input[name="q-${q.id}"]:checked`);
        return { question_id: q.id, selected_option: checked ? Number(checked.value) : -1, text_answer: "" };
      }
      return { question_id: q.id, selected_option: -1, text_answer: $(`#t-${q.id}`).value };
    });
    try {
      const result = await api(`/public/attempts/${attemptId}/submit`, {
        method: "POST",
        body: JSON.stringify({ answers }),
      });
      sessionStorage.setItem("last_result", JSON.stringify(result));
      go(`/results/${attemptId}`);
    } catch (e) {
      $("#err").textContent = e.message;
      $("#submit").disabled = false;
      $("#submit").textContent = "Тапсыру";
    }
  };
}

async function viewStudentResult(id) {
  let attempt = JSON.parse(sessionStorage.getItem("last_result") || "null");
  if (!attempt || attempt.id !== id) {
    attempt = await api(`/public/attempts/${id}`);
  }
  document.getElementById("app").innerHTML = html`${topPublic()}${renderAttempt(attempt, "/")}`;
}

async function viewCode(code) {
  document.getElementById("app").innerHTML = html`
    ${topPublic()}
    <div class="wrap" style="max-width:480px;padding:20px 0">
      <div class="panel">
        <h2>Тест: ${escapeHtml(code)}</h2>
        <label>Аты-жөні</label><input id="name" />
        <label>Сынып</label><input id="klass" />
        <p class="err" id="err"></p>
        <button class="btn" id="go" style="margin-top:12px;width:100%">Бастау</button>
      </div>
    </div>
  `;
  $("#go").onclick = async () => {
    try {
      const started = await api(`/public/tests/${encodeURIComponent(code)}/start`, {
        method: "POST",
        body: JSON.stringify({ student_name: $("#name").value.trim(), class_name: $("#klass").value.trim() }),
      });
      sessionStorage.setItem("attempt", JSON.stringify(started));
      go(`/take/${started.attempt_id}`);
    } catch (e) {
      $("#err").textContent = e.message;
    }
  };
}

async function render() {
  const path = location.pathname.replace(/\/+$/, "") || "/";
  document.getElementById("app").innerHTML = `<div class="wrap"><p>Жүктелуде…</p></div>`;
  try {
    if (path === "/") return viewHome();
    if (path === "/login") return viewAuth("login");
    if (path === "/register") return viewAuth("register");
    if (path === "/join") return viewJoin();
    if (path === "/app") return viewDash();
    if (path === "/app/materials") return viewMaterials();
    if (path === "/app/tests") return viewTests();
    if (path === "/app/tests/new") return viewTestEditor("new");
    const testResults = path.match(/^\/app\/tests\/([^/]+)\/results$/);
    if (testResults) return viewResults(testResults[1]);
    const testEdit = path.match(/^\/app\/tests\/([^/]+)$/);
    if (testEdit) return viewTestEditor(testEdit[1]);
    const tAttempt = path.match(/^\/app\/attempts\/([^/]+)$/);
    if (tAttempt) return viewTeacherAttempt(tAttempt[1]);
    const take = path.match(/^\/take\/([^/]+)$/);
    if (take) return viewTake(take[1]);
    const results = path.match(/^\/results\/([^/]+)$/);
    if (results) return viewStudentResult(results[1]);
    const code = path.match(/^\/t\/([^/]+)$/);
    if (code) return viewCode(code[1].toUpperCase());
    document.getElementById("app").innerHTML = `${topPublic()}<div class="wrap"><h1>Бет табылмады</h1></div>`;
  } catch (e) {
    document.getElementById("app").innerHTML = `<div class="wrap"><p class="err">${escapeHtml(e.message)}</p></div>`;
  }
}

document.addEventListener("click", (ev) => {
  const a = ev.target.closest("a");
  if (!a) return;
  const href = a.getAttribute("href");
  if (!href || href.startsWith("http") || href.startsWith(API) || a.hasAttribute("data-dl")) return;
  if (href === "/" && a.id === "logout") {
    ev.preventDefault();
    state.token = "";
    state.teacher = null;
    localStorage.removeItem("mektep_token");
    go("/");
    return;
  }
  if (href.startsWith("/")) {
    ev.preventDefault();
    go(href);
  }
});

render();
