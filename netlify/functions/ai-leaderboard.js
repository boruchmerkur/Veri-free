// netlify/functions/ai-leaderboard.js
// Serves the arena.ai agent-leaderboard as slim JSON at /api/ai-leaderboard.
//
// arena.ai has no public API; the leaderboard data is server-rendered into the
// page as Next.js RSC flight chunks (self.__next_f.push strings). This function
// fetches the page, joins the chunks, extracts the leaderboard array with a
// balanced-bracket scan, and returns only the fields the widget needs.
//
// Caching: the CDN holds a response for 6h and serves stale for a day while
// revalidating, so arena.ai sees at most ~4 requests/day regardless of traffic.
// If the fetch or the parse ever breaks (site redesign), the baked-in snapshot
// below is served with {"stale":true} so the widget keeps working and can say
// "as of <date>" honestly.

const SOURCE = 'https://arena.ai/leaderboard/agent';

const SNAPSHOT = {"updated":"2026-07-21T06:00:00.000Z","source":"https://arena.ai/leaderboard/agent","models":[{"rank":1,"model":"Claude Fable 5 (High)","org":"Anthropic","license":"Proprietary","url":"https://www.anthropic.com/news/claude-fable-5-mythos-5","score":0.12719,"ci":0.02002,"sessions":23549,"signals":{"task_outcome_explicit":0.10674,"praise_complaint":0.23936,"steerability":0.14625,"bash_recovery_steps":0.12972,"tool_hallucination":0.01389}},{"rank":2,"model":"GPT 5.6 Sol (xHigh)","org":"OpenAI","license":"Proprietary","url":"https://openai.com/index/gpt-5-6/","score":0.10124,"ci":0.01694,"sessions":15991,"signals":{"task_outcome_explicit":0.07252,"praise_complaint":0.23534,"steerability":0.09707,"bash_recovery_steps":0.08738,"tool_hallucination":0.01389}},{"rank":3,"model":"Claude Opus 4.8 (Thinking)","org":"Anthropic","license":"Proprietary","url":"https://www.anthropic.com/news/claude-opus-4-8","score":0.09748,"ci":0.0139,"sessions":34147,"signals":{"task_outcome_explicit":0.08897,"praise_complaint":0.19415,"steerability":0.09776,"bash_recovery_steps":0.10432,"tool_hallucination":0.00221}},{"rank":4,"model":"Kimi K3","org":"Moonshot","license":"Proprietary","url":"https://platform.kimi.ai/docs/guide/kimi-k3-quickstart","score":0.09708,"ci":0.01517,"sessions":11490,"signals":{"task_outcome_explicit":0.13998,"praise_complaint":0.20299,"steerability":0.06519,"bash_recovery_steps":0.06335,"tool_hallucination":0.01389}},{"rank":5,"model":"Claude Sonnet 5 (High)","org":"Anthropic","license":"Proprietary","url":"https://www.anthropic.com/news/claude-sonnet-5","score":0.08657,"ci":0.01893,"sessions":24359,"signals":{"task_outcome_explicit":0.0814,"praise_complaint":0.16878,"steerability":0.06202,"bash_recovery_steps":0.10813,"tool_hallucination":0.01251}},{"rank":6,"model":"GPT 5.5 (xHigh)","org":"OpenAI","license":"Proprietary","url":"https://openai.com/index/introducing-gpt-5-5/","score":0.08412,"ci":0.00866,"sessions":40667,"signals":{"task_outcome_explicit":0.06648,"praise_complaint":0.1108,"steerability":0.08176,"bash_recovery_steps":0.14766,"tool_hallucination":0.01389}},{"rank":7,"model":"Claude Opus 4.7 (Thinking)","org":"Anthropic","license":"Proprietary","url":"https://www.anthropic.com/news/claude-opus-4-7","score":0.07938,"ci":0.01237,"sessions":35151,"signals":{"task_outcome_explicit":0.05665,"praise_complaint":0.11551,"steerability":0.08624,"bash_recovery_steps":0.1257,"tool_hallucination":0.0128}},{"rank":8,"model":"Claude Opus 4.7","org":"Anthropic","license":"Proprietary","url":"https://www.anthropic.com/news/claude-opus-4-7","score":0.07669,"ci":0.01252,"sessions":35672,"signals":{"task_outcome_explicit":0.04966,"praise_complaint":0.12479,"steerability":0.08948,"bash_recovery_steps":0.10623,"tool_hallucination":0.01331}},{"rank":9,"model":"GPT 5.5 (High)","org":"OpenAI","license":"Proprietary","url":"https://openai.com/index/introducing-gpt-5-5/","score":0.0761,"ci":0.00807,"sessions":65859,"signals":{"task_outcome_explicit":0.06197,"praise_complaint":0.09796,"steerability":0.08768,"bash_recovery_steps":0.11898,"tool_hallucination":0.01389}},{"rank":10,"model":"GLM 5.2 (Max)","org":"Z.ai","license":"MIT","url":"https://huggingface.co/zai-org/GLM-5.2","score":0.06495,"ci":0.01,"sessions":38221,"signals":{"task_outcome_explicit":0.08654,"praise_complaint":0.12943,"steerability":0.04715,"bash_recovery_steps":0.04775,"tool_hallucination":0.01389}},{"rank":11,"model":"Claude Opus 4.6","org":"Anthropic","license":"Proprietary","url":"https://www.anthropic.com/news/claude-opus-4-6","score":0.06423,"ci":0.01236,"sessions":34862,"signals":{"task_outcome_explicit":0.03117,"praise_complaint":0.09939,"steerability":0.06526,"bash_recovery_steps":0.11143,"tool_hallucination":0.01387}},{"rank":12,"model":"GPT 5.5","org":"OpenAI","license":"Proprietary","url":"https://openai.com/index/introducing-gpt-5-5/","score":0.05654,"ci":0.00763,"sessions":66796,"signals":{"task_outcome_explicit":0.03923,"praise_complaint":0.05665,"steerability":0.06075,"bash_recovery_steps":0.11219,"tool_hallucination":0.01389}},{"rank":13,"model":"GPT 5.4 (High)","org":"OpenAI","license":"Proprietary","url":"https://platform.openai.com/docs/models/gpt-5.4","score":0.05643,"ci":0.00767,"sessions":66142,"signals":{"task_outcome_explicit":0.0623,"praise_complaint":0.03133,"steerability":0.07749,"bash_recovery_steps":0.09716,"tool_hallucination":0.01389}},{"rank":14,"model":"Grok 4.5","org":"SpaceXAI","license":"Proprietary","url":"https://docs.x.ai/developers/models/grok-4.5","score":0.05557,"ci":0.01326,"sessions":21424,"signals":{"task_outcome_explicit":0.03864,"praise_complaint":0.08169,"steerability":0.03803,"bash_recovery_steps":0.10559,"tool_hallucination":0.01389}},{"rank":15,"model":"Claude Opus 4.8","org":"Anthropic","license":"Proprietary","url":"https://www.anthropic.com/news/claude-opus-4-8","score":0.03565,"ci":0.01651,"sessions":32216,"signals":{"task_outcome_explicit":0.07101,"praise_complaint":0.11631,"steerability":0.08251,"bash_recovery_steps":0.09817,"tool_hallucination":-0.18977}},{"rank":16,"model":"Claude Sonnet 4.6","org":"Anthropic","license":"Proprietary","url":"https://www.anthropic.com/news/claude-sonnet-4-6","score":0.02838,"ci":0.01149,"sessions":35646,"signals":{"task_outcome_explicit":-0.00618,"praise_complaint":0.00654,"steerability":0.01353,"bash_recovery_steps":0.11449,"tool_hallucination":0.01353}},{"rank":17,"model":"GLM 5.1","org":"Z.ai","license":"MIT","url":"https://huggingface.co/zai-org/GLM-5.1","score":0.01426,"ci":0.00785,"sessions":57532,"signals":{"task_outcome_explicit":0.01118,"praise_complaint":0.0099,"steerability":-0.00153,"bash_recovery_steps":0.03786,"tool_hallucination":0.01389}},{"rank":18,"model":"Muse Spark 1.1","org":"Meta","license":"Proprietary","url":"https://ai.meta.com/blog/introducing-muse-spark-meta-model-api/","score":0.00669,"ci":0.0089,"sessions":28128,"signals":{"task_outcome_explicit":0.04395,"praise_complaint":-0.04301,"steerability":-0.04503,"bash_recovery_steps":0.06395,"tool_hallucination":0.01359}},{"rank":19,"model":"Qwen3.7 Max","org":"Alibaba","license":"Proprietary","url":null,"score":0.0009,"ci":0.01067,"sessions":15992,"signals":{"task_outcome_explicit":-0.01837,"praise_complaint":-0.05728,"steerability":-0.00019,"bash_recovery_steps":0.072,"tool_hallucination":0.00833}},{"rank":20,"model":"Gemini 3.1 Pro Preview","org":"Google","license":"Proprietary","url":"https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-pro/","score":-0.00475,"ci":0.00677,"sessions":67658,"signals":{"task_outcome_explicit":0.02045,"praise_complaint":0.00556,"steerability":0.01992,"bash_recovery_steps":-0.08289,"tool_hallucination":0.01322}},{"rank":21,"model":"Qwen3.7 Plus","org":"Alibaba","license":"Proprietary","url":"https://qwen.ai/blog?id=qwen3.7-plus","score":-0.00757,"ci":0.01247,"sessions":12816,"signals":{"task_outcome_explicit":-0.01744,"praise_complaint":-0.065,"steerability":-0.01414,"bash_recovery_steps":0.0558,"tool_hallucination":0.00295}},{"rank":22,"model":"Kimi K2.7 Code","org":"Moonshot","license":"Modified MIT","url":null,"score":-0.01019,"ci":0.01691,"sessions":10082,"signals":{"task_outcome_explicit":0.03791,"praise_complaint":0.00955,"steerability":-0.0837,"bash_recovery_steps":-0.0286,"tool_hallucination":0.01389}},{"rank":23,"model":"Gemini 3.5 Flash (High)","org":"Google","license":"Proprietary","url":"https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-5/","score":-0.01027,"ci":0.00802,"sessions":45992,"signals":{"task_outcome_explicit":0.0289,"praise_complaint":-0.03946,"steerability":-0.00683,"bash_recovery_steps":-0.0192,"tool_hallucination":-0.01477}},{"rank":24,"model":"DeepSeek V4 Pro","org":"DeepSeek","license":"MIT","url":"https://api-docs.deepseek.com/news/news260424","score":-0.01186,"ci":0.01061,"sessions":16514,"signals":{"task_outcome_explicit":-0.04798,"praise_complaint":-0.05654,"steerability":-0.02114,"bash_recovery_steps":0.0576,"tool_hallucination":0.00874}},{"rank":25,"model":"Hy3","org":"Tencent","license":"Apache 2.0","url":null,"score":-0.02234,"ci":0.02872,"sessions":3530,"signals":{"task_outcome_explicit":-0.04648,"praise_complaint":-0.02871,"steerability":-0.071,"bash_recovery_steps":0.02556,"tool_hallucination":0.00894}},{"rank":26,"model":"Kimi K2.6","org":"Moonshot","license":"Modified MIT","url":"https://www.kimi.com/blog/kimi-k2-6","score":-0.02573,"ci":0.01748,"sessions":10139,"signals":{"task_outcome_explicit":0.0167,"praise_complaint":-0.03035,"steerability":-0.06719,"bash_recovery_steps":-0.06168,"tool_hallucination":0.01389}},{"rank":27,"model":"Minimax M3","org":"MiniMax","license":"MiniMax Community License","url":"https://www.minimax.io/models/text/m3","score":-0.03102,"ci":0.01048,"sessions":16030,"signals":{"task_outcome_explicit":-0.0749,"praise_complaint":-0.09668,"steerability":-0.05434,"bash_recovery_steps":0.06155,"tool_hallucination":0.00926}},{"rank":28,"model":"Mimo V2.5 Pro","org":"Xiaomi","license":"MIT","url":"https://mimo.xiaomi.com/mimo-v2-5-pro/","score":-0.03393,"ci":0.01106,"sessions":16479,"signals":{"task_outcome_explicit":-0.05876,"praise_complaint":-0.10332,"steerability":-0.0294,"bash_recovery_steps":0.01693,"tool_hallucination":0.0049}},{"rank":29,"model":"DeepSeek V4 Flash","org":"DeepSeek","license":"MIT","url":"https://api-docs.deepseek.com/news/news260424","score":-0.03492,"ci":0.01055,"sessions":16015,"signals":{"task_outcome_explicit":-0.06552,"praise_complaint":-0.0975,"steerability":-0.04156,"bash_recovery_steps":0.03461,"tool_hallucination":-0.00465}},{"rank":30,"model":"Inkling","org":"Thinky","license":"Apache 2.0","url":"https://thinkingmachines.ai/news/introducing-inkling/","score":-0.06414,"ci":0.01309,"sessions":10678,"signals":{"task_outcome_explicit":-0.07189,"praise_complaint":-0.19009,"steerability":-0.116,"bash_recovery_steps":0.06122,"tool_hallucination":-0.00396}},{"rank":31,"model":"Gemini 3.5 Flash (Medium)","org":"Google","license":"Proprietary","url":"https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-5/","score":-0.06798,"ci":0.01691,"sessions":8641,"signals":{"task_outcome_explicit":-0.13177,"praise_complaint":-0.08241,"steerability":-0.10196,"bash_recovery_steps":-0.0328,"tool_hallucination":0.00905}},{"rank":32,"model":"Grok Build 0.1","org":"SpaceXAI","license":"Proprietary","url":null,"score":-0.08005,"ci":0.00809,"sessions":59109,"signals":{"task_outcome_explicit":-0.04598,"praise_complaint":-0.1193,"steerability":-0.12258,"bash_recovery_steps":-0.12022,"tool_hallucination":0.00781}},{"rank":33,"model":"Grok 4.3 (High)","org":"SpaceXAI","license":"Proprietary","url":"https://docs.x.ai/developers/models/grok-4.3","score":-0.08245,"ci":0.00806,"sessions":47866,"signals":{"task_outcome_explicit":-0.08717,"praise_complaint":-0.14908,"steerability":-0.07314,"bash_recovery_steps":-0.11369,"tool_hallucination":0.01081}},{"rank":34,"model":"Gemini 3 Flash","org":"Google","license":"Proprietary","url":"https://blog.google/products/gemini/gemini-3-flash","score":-0.08647,"ci":0.00756,"sessions":68372,"signals":{"task_outcome_explicit":-0.08735,"praise_complaint":-0.1232,"steerability":-0.05332,"bash_recovery_steps":-0.16879,"tool_hallucination":0.00032}},{"rank":35,"model":"Minimax M2.7","org":"MiniMax","license":"Modified MIT","url":"https://www.minimax.io/news/minimax-m27-en","score":-0.12472,"ci":0.01337,"sessions":16212,"signals":{"task_outcome_explicit":-0.17128,"praise_complaint":-0.15663,"steerability":-0.17455,"bash_recovery_steps":-0.1335,"tool_hallucination":0.01233}},{"rank":36,"model":"Nemotron 3 Ultra","org":"Nvidia","license":"OpenMDW-1.1","url":null,"score":-0.13503,"ci":0.02381,"sessions":10263,"signals":{"task_outcome_explicit":-0.15083,"praise_complaint":-0.12199,"steerability":-0.21372,"bash_recovery_steps":-0.1877,"tool_hallucination":-0.00092}},{"rank":37,"model":"Gemma 4 31B","org":"Google","license":"Apache 2.0","url":"https://aistudio.google.com/app/prompts/new_chat?model=gemma-4-31b-it","score":-0.14507,"ci":0.01604,"sessions":54817,"signals":{"task_outcome_explicit":-0.02309,"praise_complaint":-0.04488,"steerability":-0.06872,"bash_recovery_steps":-0.33534,"tool_hallucination":-0.2533}},{"rank":38,"model":"Grok 4.3","org":"SpaceXAI","license":"Proprietary","url":"https://docs.x.ai/developers/models/grok-4.3","score":-0.15043,"ci":0.01033,"sessions":67800,"signals":{"task_outcome_explicit":-0.10924,"praise_complaint":-0.16201,"steerability":-0.07793,"bash_recovery_steps":-0.41508,"tool_hallucination":0.01213}}]};

function extract(html) {
  const re = /self\.__next_f\.push\(\[1,\s*"((?:[^"\\]|\\.)*)"\]\)/g;
  let blob = '', m;
  while ((m = re.exec(html))) blob += JSON.parse('"' + m[1] + '"');

  const start = blob.indexOf('[{"rank":1,"contenderName"');
  if (start < 0) throw new Error('leaderboard marker not found');

  let depth = 0, inStr = false, esc = false, end = -1;
  for (let i = start; i < blob.length; i++) {
    const ch = blob[i];
    if (inStr) {
      if (esc) esc = false;
      else if (ch === '\\') esc = true;
      else if (ch === '"') inStr = false;
      continue;
    }
    if (ch === '"') inStr = true;
    else if (ch === '[' || ch === '{') depth++;
    else if (ch === ']' || ch === '}') { depth--; if (depth === 0) { end = i + 1; break; } }
  }
  if (end < 0) throw new Error('unbalanced leaderboard payload');

  const rows = JSON.parse(blob.slice(start, end));
  const up = blob.match(/"lastUpdated":"([^"]+)"/);

  const models = rows.map((r) => ({
    rank: r.rank,
    model: r.model,
    org: r.modelOrganization,
    license: r.license || null,
    url: r.modelUrl || null,
    score: r.avgScore ? r.avgScore.value : null,
    ci: r.avgScore ? r.avgScore.ci : null,
    sessions: r.sessions || null,
    signals: r.signalScores || {}
  }));

  // sanity: a redesign that half-breaks the parse must not replace good data
  if (models.length < 10 || typeof models[0].score !== 'number' || models[0].rank !== 1)
    throw new Error('parsed data failed sanity check');

  return { updated: up ? up[1] : null, source: SOURCE, models };
}

export default async (req) => {
  const headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Cache-Control': 'public, max-age=3600',
    'Netlify-CDN-Cache-Control': 'public, s-maxage=21600, stale-while-revalidate=86400'
  };
  try {
    const res = await fetch(SOURCE, {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; checkmysite-ai-widget; +https://checkmysite.pro/ai/)' },
      signal: AbortSignal.timeout(15000)
    });
    if (!res.ok) throw new Error('upstream ' + res.status);
    const data = extract(await res.text());
    return new Response(JSON.stringify(data), { status: 200, headers });
  } catch (e) {
    console.error('ai-leaderboard: fell back to snapshot —', e.message);
    // shorter CDN hold so a transient upstream failure clears quickly
    return new Response(JSON.stringify({ ...SNAPSHOT, stale: true }), {
      status: 200,
      headers: { ...headers, 'Netlify-CDN-Cache-Control': 'public, s-maxage=1800, stale-while-revalidate=86400' }
    });
  }
};

export const config = { path: '/api/ai-leaderboard' };
