<script>
  let username = 'processor'
  let password = 'herb123456'
  let token = localStorage.getItem('herb_token') || ''
  let role = localStorage.getItem('herb_role') || ''
  let rows = []
  let herb = '白芍'
  let tempC = 105
  let minutes = 9
  let error = ''
  let detail = null
  let detailId = null

  async function api(path, options = {}) {
    const res = await fetch(path, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.detail || '请求失败')
    return data
  }

  function fryStep(doc) {
    return (doc?.steps || []).find((s) => s.name === '清炒') || doc?.steps?.[0] || {}
  }

  async function enter() {
    const data = await api('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
    token = data.access_token
    role = data.role
    localStorage.setItem('herb_token', token)
    localStorage.setItem('herb_role', role)
    await load()
  }

  async function load() {
    rows = await api('/api/batches')
    if (detailId !== null) await openDetail(detailId)
  }

  async function save() {
    error = ''
    try {
      await api('/api/batches', {
        method: 'POST',
        body: JSON.stringify({
          herb,
          steps: [{ name: '清炒', temp_c: Number(tempC), minutes: Number(minutes) }],
        }),
      })
      await load()
    } catch (err) {
      error = err.message
    }
  }

  async function openDetail(id) {
    detail = await api(`/api/batches/${id}`)
    detailId = id
  }

  function closeDetail() {
    detail = null
    detailId = null
  }

  function leave() {
    localStorage.clear()
    token = ''
    role = ''
    detail = null
    detailId = null
  }

  if (token) load()
</script>

<main>
  <h1>饮片炮制记录台</h1>
  {#if !token}
    <p>炮制记录整包保存。清炒温度须在 80 到 150，时长须在 5 到 30 分钟。</p>
    <input bind:value={username} />
    <input type="password" bind:value={password} />
    <button on:click={enter}>登录</button>
    <p>processor / herb123456 可写；checker / check123456 只读</p>
  {:else}
    <p>
      <button on:click={leave}>退出</button>
    </p>
    {#if role === 'writer'}
      <input bind:value={herb} placeholder="饮片" />
      <input type="number" bind:value={tempC} />
      <input type="number" bind:value={minutes} />
      <button on:click={save}>写入清炒记录</button>
      {#if error}<p>{error}</p>{/if}
    {/if}
    <ul>
      {#each rows as row}
        {@const fry = fryStep(row.doc)}
        <li>
          {row.herb} · {row.verdict} · {row.reason} · 温度 {fry.temp_c} ℃ · 时长 {fry.minutes} 分钟
          <button on:click={() => openDetail(row.id)}>详情</button>
        </li>
      {/each}
    </ul>
    {#if detail}
      <section class="detail">
        <h2>记录详情 #{detail.id}</h2>
        <p>饮片：{detail.herb}</p>
        <p>结论：{detail.verdict} · {detail.reason}</p>
        <p>录入人：{detail.created_by}</p>
        <ul>
          {#each detail.doc.steps as step}
            <li>{step.name} · 温度 {step.temp_c} ℃ · 时长 {step.minutes} 分钟</li>
          {/each}
        </ul>
        <button on:click={closeDetail}>关闭详情</button>
      </section>
    {/if}
  {/if}
</main>

<style>
  main { font-family: sans-serif; max-width: 720px; margin: 24px auto; color: #3f2f1f; }
  h1 { color: #7c2d12; }
  input { margin-right: 8px; padding: 6px; }
  li { margin: 4px 0; }
  .detail { border: 1px solid #d6c3ae; border-radius: 6px; padding: 12px 16px; margin-top: 16px; }
</style>
