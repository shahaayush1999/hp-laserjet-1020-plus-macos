/* Function: 100167a8 hp1020_elf_entry_candidate */


void entry(void)

{
  undefined1 in_INTENABLE;
  
  rsil(1);
  wsr(in_INTENABLE,0);
  wsr(0,0x11);
  rsync();
  (*DAT_10006a14)(0x11,DAT_10006a14);
  return;
}


