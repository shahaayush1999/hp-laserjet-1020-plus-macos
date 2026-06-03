/*
Function: 10011178 hp1020_get_config_value_candidate
Score: 16
*/


uint hp1020_get_config_value_candidate(int param_1)

{
  int iVar1;
  
  iVar1 = *(int *)(PTR_DAT_1000647c + param_1 * 0x18 + 8);
  if (iVar1 - 3U < 2) {
    return 0xffffffff;
  }
  if (iVar1 == 1) {
    return (uint)**(ushort **)(PTR_DAT_1000647c + param_1 * 0x18 + 4);
  }
  if (iVar1 == 0) {
    return (uint)**(byte **)(PTR_DAT_1000647c + param_1 * 0x18 + 4);
  }
  if (iVar1 != 2) {
    return param_1 * 3;
  }
  return **(uint **)(PTR_DAT_1000647c + param_1 * 0x18 + 4);
}


