/* Function: 10017b64 hp1020_sys_interface_01_candidate */


undefined4
hp1020_sys_interface_01_candidate(int *param_1,undefined4 param_2,int param_3,uint param_4)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 == DAT_10006b10)) {
    return 2;
  }
  if (param_3 == 0) {
    return 3;
  }
  if (99 < param_4) {
    if (*(int *)PTR_DAT_10006a9c == 0) {
      if (*(int *)PTR_DAT_10005d80 != DAT_10006a94) {
        return 0x13;
      }
    }
    else if (*(int *)PTR_DAT_10005d80 != 0) {
      return 0x13;
    }
    if (*(undefined **)PTR_DAT_10006a9c == PTR_DAT_10006ae8) {
      return 0x13;
    }
    uVar1 = FUN_10018f64(param_1,param_2,param_3,param_4);
    return uVar1;
  }
  return 5;
}


