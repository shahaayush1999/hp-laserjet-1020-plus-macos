/* Function: 1001816c hp1020_object_target_1001816c */


undefined4 hp1020_object_target_1001816c(int *param_1)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 != DAT_100065bc)) {
    return 0xc;
  }
  if ((*(undefined **)PTR_DAT_10006a9c != (undefined *)0x0) &&
     ((*(int *)PTR_DAT_10005d80 == 0 && (*(undefined **)PTR_DAT_10006a9c != PTR_DAT_10006ae8)))) {
    uVar1 = FUN_1001a3c4(param_1);
    return uVar1;
  }
  return 0x13;
}


