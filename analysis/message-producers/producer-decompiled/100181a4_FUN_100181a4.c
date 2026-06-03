/* Function: 100181a4 FUN_100181a4 */


undefined4 FUN_100181a4(int *param_1,int param_2)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 != DAT_100065bc)) {
    return 0xc;
  }
  if ((param_2 != 0) &&
     ((*(int *)PTR_DAT_10005d80 != 0 || (*(undefined **)PTR_DAT_10006a9c == PTR_DAT_10006ae8)))) {
    return 4;
  }
  uVar1 = FUN_1001a478(param_1,param_2);
  return uVar1;
}


