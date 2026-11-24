import {describe,expect,it} from 'vitest';
import {validApplicationData} from './application-sandbox';
describe('application storage bounds',()=>{
 it('accepts structured application JSON only',()=>{expect(validApplicationData('[{"title":"note","done":false}]')).toBe(true);expect(validApplicationData('null')).toBe(false);expect(validApplicationData('"secret"')).toBe(false);expect(validApplicationData('{')).toBe(false);});
 it('rejects dangerous keys, huge values and excessive nesting',()=>{expect(validApplicationData('{"__proto__":{}}')).toBe(false);expect(validApplicationData(JSON.stringify(['x'.repeat(200001)]))).toBe(false);expect(validApplicationData('['.repeat(25)+'0'+']'.repeat(25))).toBe(false);});
});
