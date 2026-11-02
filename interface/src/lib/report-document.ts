/** Restricted report Markdown projection. No HTML, URLs or executable content. */
export type ReportBlock={kind:'heading';text:string;level:number}|{kind:'paragraph';text:string}|{kind:'list';items:string[]}|{kind:'table';headers:string[];rows:string[][]};
const decode=(value:string)=>value.replaceAll('<br>','\n').replaceAll('&#124;','|').replaceAll('&lt;','<').replaceAll('&gt;','>').replaceAll('&amp;','&');
const cells=(line:string)=>line.trim().replace(/^\||\|$/g,'').split('|').map(v=>decode(v.trim()));
export function reportDocument(markdown:string):ReportBlock[]{
 const lines=markdown.replaceAll('\r','').split('\n'),blocks:ReportBlock[]=[];
 for(let i=0;i<lines.length;i++){
  const line=lines[i].trim();if(!line)continue;
  const heading=/^(#{1,3})\s+(.+)$/.exec(line);
  if(heading){blocks.push({kind:'heading',level:heading[1].length,text:decode(heading[2])});continue;}
  if(line.startsWith('|')&&/^\|[\s:|\-]+\|$/.test(lines[i+1]?.trim()??'')){
   const headers=cells(line),rows:string[][]=[];i++;
   while(lines[i+1]?.trim().startsWith('|')){const row=cells(lines[++i]);rows.push(headers.map((_,j)=>row[j]??''));}
   blocks.push({kind:'table',headers,rows});continue;
  }
  if(line.startsWith('- ')){
   const items=[decode(line.slice(2))];while(lines[i+1]?.trim().startsWith('- '))items.push(decode(lines[++i].trim().slice(2)));
   blocks.push({kind:'list',items});continue;
  }
  blocks.push({kind:'paragraph',text:decode(line)});
 }
 return blocks;
}
export function downloadBlob(blob:Blob,filename:string){
 const url=URL.createObjectURL(blob),anchor=document.createElement('a');anchor.href=url;anchor.download=filename;
 document.body.appendChild(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
