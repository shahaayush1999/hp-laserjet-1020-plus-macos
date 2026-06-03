/* Function: 1001b668 FUN_1001b668 */


/* WARNING: Control flow encountered bad instruction data */

uint FUN_1001b668(uint param_1,uint param_2)

{
  if (param_2 < 2) {
    if (param_2 != 0) {
      return param_1;
    }
    return 0;
  }
  if ((uint)LZCOUNT(param_1) < (uint)LZCOUNT(param_2)) {
                    /* WARNING: Bad instruction - Truncating control flow here */
    halt_baddata();
  }
  return (uint)(param_2 <= param_1);
}


