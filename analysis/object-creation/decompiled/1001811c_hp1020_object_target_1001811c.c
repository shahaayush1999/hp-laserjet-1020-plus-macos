/* Function: 1001811c hp1020_object_target_1001811c */


undefined4 hp1020_object_target_1001811c(int *param_1,undefined4 param_2,undefined4 param_3)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 == DAT_100065bc)) {
    return 0xc;
  }
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
  uVar1 = FUN_1001a380(param_1,param_2,param_3);
  return uVar1;
}


