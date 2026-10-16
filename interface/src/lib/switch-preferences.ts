// Browser-wide preferences, independent of conversation identity or stored context.
export const CHAT_MEMORY_KEY = 'actioncharter:chat-memory:v2';
export const LIBRARY_PRIVATE_KEY = 'actioncharter:library-private:v1';
export function loadSwitchPreference(key:string,fallback:boolean):boolean {
  try { const saved=localStorage.getItem(key);return saved==='on'?true:saved==='off'?false:fallback; }
  catch { return fallback; }
}
export function saveSwitchPreference(key:string,value:boolean):void {
  try { localStorage.setItem(key,value?'on':'off'); } catch { /* Keep the in-memory selection when storage is blocked. */ }
}
export function loadChatMemory(conversationId:string):boolean {
  try {
    const saved=localStorage.getItem(CHAT_MEMORY_KEY);
    if(saved==='on'||saved==='off')return saved==='on';
    // Adopt the currently open chat's old setting once; later chat changes never reset it.
    const legacy=localStorage.getItem(`actioncharter:chat-memory:${conversationId}`);
    if(legacy==='on'||legacy==='off'){
      saveSwitchPreference(CHAT_MEMORY_KEY,legacy==='on');
      return legacy==='on';
    }
  } catch { /* Browser storage is optional. */ }
  return true;
}
