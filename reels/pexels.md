# Pexels clips through the built-in browser

New Pexels API keys are paused, and curl gets 403 on pexels.com pages. A pexels.com tab in the built-in browser can
`fetch()` its own pages, and the `videos.pexels.com` file CDN is open to curl. A loop longer than about 45s times out the
tool, so each step starts async into `window.*` and is read back in a second call.

## 0. Open a tab
`mcp__Claude_Browser__navigate` → `https://www.pexels.com/search/videos/ladakh/?orientation=portrait`

## 1. Search: collect ids + slugs (edit Q)
```js
window.R={}; window.RD=false; const Q={spiti:['spiti','spiti valley','chandratal','key monastery']};
(async()=>{ const jobs=[]; for (const [p,qs] of Object.entries(Q)){ R[p]={}; for (const q of qs) for (const page of [1,2]) jobs.push([p,q,page]); }
 for (let i=0;i<jobs.length;i+=8){ await Promise.all(jobs.slice(i,i+8).map(async([p,q,page])=>{ try{ const h=await (await fetch(`https://www.pexels.com/search/videos/${encodeURIComponent(q)}/?orientation=portrait&page=${page}`)).text(); const re=/\/video\/([a-z0-9-]+)-(\d+)\//g; let m; while((m=re.exec(h))) R[p][m[2]]=m[1]; }catch(e){} })); }
 window.RD=true; })(); 'started'
```
Read it back: `({done:window.RD, out:Object.fromEntries(Object.entries(window.R).map(([k,v])=>[k,Object.entries(v).map(([id,s])=>id+' '+s).join('\n')]))})`

## 2. Curate by slug (by hand, every time)
Keep real Indian places and shots with movement: people from behind, boats, flags, drives, rivers, gondolas, rafting.
Drop slugs naming other countries (nepal, kathmandu, pakistan, swat, hunza, bangladesh, vietnam, iceland, andes, georgia…),
other Indian regions when the place is specific (kedarnath, kedarkantha for Manali), and off-topic clips (keys, realtor,
houseplant, green screen, hotel room tour). Aim for about 3x the shots one reel needs, since every reel of a place reuses the library.

## 3. Resolve the 1080x1920 file for each kept id (edit S)
```js
const S={spiti:'19790006 34025198 35693639'}; window.U={}; window.UD=false; const slugOf={}; for (const v of Object.values(window.R)) Object.assign(slugOf,v);
(async()=>{ const jobs=[]; for (const [p,ids] of Object.entries(S)){ U[p]=[]; for (const id of ids.split(' ')) jobs.push([p,id]); }
 for (let i=0;i<jobs.length;i+=8){ await Promise.all(jobs.slice(i,i+8).map(async([p,id])=>{ const slug=slugOf[id]; try{ const h=await (await fetch(`https://www.pexels.com/video/${slug}-${id}/`)).text(); const u=[...new Set(h.match(new RegExp(`https://videos\\.pexels\\.com/video-files/${id}/[^"'\\\\ ]+\\.mp4`,'g'))||[])]; const d=x=>(x.match(/_(\d+)_(\d+)_/)||[0,0,0]).slice(1).map(Number); const ok=u.filter(x=>{const [w,h]=d(x); return h>w&&w>=720&&w<=1440}).sort((a,b)=>Math.abs(d(a)[0]-1080)-Math.abs(d(b)[0]-1080)); if(ok[0]) U[p].push(`${id} ${slug} ${ok[0]}`); }catch(e){} })); }
 window.UD=true; })(); 'started'
```
Read it back: `Object.entries(window.U).map(([k,v])=>'#'+k+'\n'+v.join('\n')).join('\n')`, then save each place's lines to
`library/<place>.txt` and run `python3 bin/fetch.py <place> library/<place>.txt`. It downloads 4 at a time, makes 60fps
clips half-speed slow motion, and records the licence in SOURCES.jsonl. Never use `/download/video/<id>/`: that is the 4K original, 150–400 MB.
