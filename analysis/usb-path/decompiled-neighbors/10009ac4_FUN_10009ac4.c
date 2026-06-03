/*
Function: 10009ac4 FUN_10009ac4
Score: 2
*/


short * FUN_10009ac4(short *param_1,byte *param_2)

{
  short *psVar1;
  
  psVar1 = param_1;
  do {
    *psVar1 = (ushort)*param_2 << 8;
    param_2 = param_2 + 1;
    psVar1 = psVar1 + 1;
  } while (*param_2 != 0);
  return param_1;
}


