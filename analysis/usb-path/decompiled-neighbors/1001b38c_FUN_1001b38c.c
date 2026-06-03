/*
Function: 1001b38c FUN_1001b38c
Score: 0
*/


/* WARNING: Control flow encountered bad instruction data */

void FUN_1001b38c(undefined1 *param_1,undefined1 *param_2,uint param_3)

{
  undefined1 uVar1;
  undefined1 uVar2;
  
  if (((uint)param_1 & 1) != 0) {
    if (param_3 < 7) {
      halt_baddata();
    }
    uVar1 = *param_2;
    param_2 = param_2 + 1;
    param_3 = param_3 - 1;
    *param_1 = uVar1;
    param_1 = param_1 + 1;
  }
  if (((uint)param_1 & 2) != 0) {
    if (param_3 < 6) {
                    /* WARNING: Bad instruction - Truncating control flow here */
      halt_baddata();
    }
    uVar1 = *param_2;
    uVar2 = param_2[1];
    param_2 = param_2 + 2;
    param_3 = param_3 - 2;
    *param_1 = uVar1;
    param_1[1] = uVar2;
  }
  if (((uint)param_2 & 3) != 0) {
    if (param_3 == 0) {
      return;
    }
                    /* WARNING: Bad instruction - Truncating control flow here */
    halt_baddata();
  }
                    /* WARNING: Bad instruction - Truncating control flow here */
  halt_baddata();
}


