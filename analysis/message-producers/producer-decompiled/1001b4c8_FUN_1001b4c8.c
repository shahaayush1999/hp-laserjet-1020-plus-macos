/* Function: 1001b4c8 FUN_1001b4c8 */


/* WARNING: Control flow encountered bad instruction data */

void FUN_1001b4c8(undefined2 *param_1,undefined1 param_2,uint param_3)

{
  if (((uint)param_1 & 3) != 0) {
    if (param_3 < 8) {
                    /* WARNING: Bad instruction - Truncating control flow here */
      halt_baddata();
    }
    if (((uint)param_1 & 1) != 0) {
      *(undefined1 *)param_1 = param_2;
      param_1 = (undefined2 *)((int)param_1 + 1);
      param_3 = param_3 - 1;
      if (((uint)param_1 & 2) == 0) goto LAB_1001b4e1;
    }
    *param_1 = CONCAT11(param_2,param_2);
    param_3 = param_3 - 2;
  }
LAB_1001b4e1:
  if (param_3 == 0) {
    return;
  }
                    /* WARNING: Bad instruction - Truncating control flow here */
  halt_baddata();
}


