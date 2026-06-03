/* Function: 10017dac FUN_10017dac */


undefined4 FUN_10017dac(int *param_1,undefined4 param_2,int param_3)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 != DAT_100065a8)) {
    return 6;
  }
  if ((param_3 != 2) && (param_3 != 0)) {
    return 8;
  }
  uVar1 = FUN_1001896c(param_1,param_2,param_3);
  return uVar1;
}


