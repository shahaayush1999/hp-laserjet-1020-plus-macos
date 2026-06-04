/* Function: 10017dd8 hp1020_object_target_10017dd8 */


undefined4 hp1020_object_target_10017dd8(int *param_1,undefined4 param_2,uint param_3)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 == DAT_100065d0)) {
    return 0x1c;
  }
  if (1 < param_3) {
    return 0x1f;
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
  uVar1 = FUN_10019538(param_1,param_2,param_3);
  return uVar1;
}


