/*
Function: 100169d4 hp1020_strlen_like
Score: 4
*/


/* WARNING: Control flow encountered bad instruction data */

char * hp1020_strlen_like(char *param_1)

{
  char *pcVar1;
  char *pcVar2;
  
  pcVar2 = param_1 + -4;
  pcVar1 = param_1;
  if ((((uint)param_1 & 1) != 0) && (pcVar2 = param_1 + -3, pcVar1 = pcVar2, *param_1 == '\0')) {
    return (char *)0x0;
  }
  if (((uint)pcVar1 & 2) != 0) {
    if ((*(uint *)(pcVar2 + 2) & DAT_10005f74) == 0) {
      return pcVar2 + (4 - (int)param_1);
    }
    if ((*(uint *)(pcVar2 + 2) & DAT_10006a24) == 0) {
      return pcVar2 + (5 - (int)param_1);
    }
  }
                    /* WARNING: Bad instruction - Truncating control flow here */
  halt_baddata();
}


