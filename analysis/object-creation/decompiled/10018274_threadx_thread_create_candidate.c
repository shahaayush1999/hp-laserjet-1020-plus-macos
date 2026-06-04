/* Function: 10018274 threadx_thread_create_candidate */


undefined4
threadx_thread_create_candidate
          (int *param_1,undefined4 param_2,int param_3,undefined4 param_4,int param_5,uint param_6,
          uint param_7,uint param_8,undefined4 param_9,uint param_10)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 == DAT_10006b14)) {
    return 0xe;
  }
  if ((param_5 == 0) || (param_3 == 0)) {
    return 3;
  }
  if (param_6 < 200) {
    return 5;
  }
  if (0x1f < param_7) {
    return 0xf;
  }
  if (param_7 < param_8) {
    return 0x18;
  }
  if (param_10 < 2) {
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
    uVar1 = threadx_thread_create_core_candidate
                      (param_1,param_2,param_3,param_4,param_5,param_6,param_7,param_8,param_9,
                       param_10);
    return uVar1;
  }
  return 0x10;
}


