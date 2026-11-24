import { afterEach,describe,expect,it,vi } from 'vitest';
import {safeModelOrigin,testServerModel} from './model';
afterEach(()=>vi.unstubAllGlobals());
describe('V1.2 server configuration adapter',()=>{
 it('returns exact HTTPS origin',()=>expect(safeModelOrigin('https://api.openai.com/v1')).toBe('https://api.openai.com'));
 it.each(['http://localhost/v1','https://u:p@api.openai.com/v1','https://api.openai.com/v1?key=a','https://api.openai.com/v1#key'])('rejects unsafe URL %s',url=>expect(()=>safeModelOrigin(url)).toThrow());
 it('only submits Key to protected platform configuration endpoint, never provider from browser',async()=>{const fetcher=vi.fn().mockResolvedValue({ok:true,status:200,json:async()=>({draft_id:'fixture',status:'passed'})});vi.stubGlobal('fetch',fetcher);await testServerModel({provider:'openai',api_key:'test-placeholder',base_url:'https://api.openai.com/v1',model:'fixture',idempotency_key:'fixture',consent:true});expect(fetcher.mock.calls[0][0]).toBe('/api/model-config/test');expect(fetcher).toHaveBeenCalledTimes(1);expect(fetcher.mock.calls[0][1].credentials).toBe('include');});
});
