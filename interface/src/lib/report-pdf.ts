import type {Content,TDocumentDefinitions} from 'pdfmake/interfaces';
import type {StatisticalFigure} from './statistical-figures';
import {reportDocument} from './report-document';
/** Lazy PDF generation: all code/fonts bundled locally, no upload or remote assets. */
export async function reportPdf(markdown:string,figures:StatisticalFigure[]=[] ):Promise<Blob>{
 const [{default:pdfMake},{default:fontFiles}]=await Promise.all([import('pdfmake/build/pdfmake'),import('pdfmake/build/vfs_fonts')]);
 const content:Content[]=[];
 for(const block of reportDocument(markdown)){
  if(block.kind==='heading')content.push({text:block.text,fontSize:block.level===1?22:block.level===2?16:12,bold:true,color:'#164e63',margin:[0,block.level===1?0:14,0,8]});
  else if(block.kind==='paragraph')content.push({text:block.text,margin:[0,0,0,7]});
  else if(block.kind==='list')content.push({ul:block.items,margin:[0,0,0,8]});
  else{
   // Wide matrices are partitioned by columns, retaining every row and its label.
   const slices=block.headers.length<=7?[block.headers.map((_,i)=>i)]:Array.from({length:Math.ceil((block.headers.length-1)/6)},(_,part)=>[0,...Array.from({length:Math.min(6,block.headers.length-1-part*6)},(_,i)=>1+part*6+i)]);
   for(const indices of slices){
    if(slices.length>1)content.push({text:`Matrix columns ${indices[1]}–${indices.at(-1)}`,italics:true,margin:[0,5,0,5]});
    content.push({table:{headerRows:1,widths:indices.map(()=>'*'),body:[indices.map(i=>({text:block.headers[i],bold:true,color:'#164e63',fillColor:'#e8f3f5'})),...block.rows.map(row=>indices.map(i=>row[i]??''))]},layout:'lightHorizontalLines',fontSize:9,margin:[0,0,0,12]});
   }
  }
 }
 for(const figure of figures){const height=Number(/height="([0-9.]+)"/.exec(figure.svg)?.[1]??400);content.push({text:figure.title,fontSize:16,bold:true,pageBreak:'before',margin:[0,0,0,12]},{svg:figure.svg,width:Math.min(680,400*760/height)},{text:figure.caption,margin:[0,12,0,12]});}
 const definition:TDocumentDefinitions={info:{title:'ActionCharter statistical analysis',author:'ActionCharter'},pageSize:'A4',pageOrientation:'landscape',pageMargins:[36,32,36,38],defaultStyle:{font:'Roboto',fontSize:10,lineHeight:1.2,color:'#172b36'},content,
  footer:(page,count)=>({text:`ActionCharter · recorded statistical report · ${page} / ${count}`,fontSize:8,color:'#566975',alignment:'right',margin:[36,10,36,0]})};
 return new Promise((resolve,reject)=>{try{pdfMake.createPdf(definition,undefined,undefined,fontFiles as unknown as Record<string,string>).getBlob(resolve);}catch(error){reject(error);}});
}
