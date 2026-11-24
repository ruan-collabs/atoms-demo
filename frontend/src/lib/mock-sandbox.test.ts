import {describe,it,expect} from 'vitest';
import {validMockData} from './mock-sandbox';
describe('mock sandbox restricted data bridge',()=>{
 it('accepts only bounded task data',()=>{expect(validMockData(JSON.stringify([{id:'1',title:'任务',completed:false}]))).toBe(true);});
 it('rejects malformed, credential fields and large input',()=>{for(const data of ['{}','not-json',JSON.stringify([{id:'1',title:'a',completed:false,api_key:'x'}]),'x'.repeat(100001)])expect(validMockData(data)).toBe(false);});
});
