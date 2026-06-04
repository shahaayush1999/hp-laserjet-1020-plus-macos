/* Function: 10017e2c hp1020_object_target_10017e2c */


undefined4 hp1020_object_target_10017e2c(int *param_1)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 != DAT_100065d0)) {
    return 0x1c;
  }
  if ((*(undefined **)PTR_DAT_10006a9c != (undefined *)0x0) &&
     ((*(int *)PTR_DAT_10005d80 == 0 && (*(undefined **)PTR_DAT_10006a9c != PTR_DAT_10006ae8)))) {
    uVar1 = FUN_10019580(param_1);
    return uVar1;
  }
  return 0x13;
}


