/* Function: 1000f228 hp1020_video_work_create_candidate */


void hp1020_video_work_create_candidate(void)

{
  int iVar1;

  iVar1 = hp1020_alloc_with_retry_candidate(0x94,1);
  hp1020_list_init_candidate(iVar1 + 0x58);
  hp1020_list_init_candidate(iVar1 + 0x50);
  hp1020_list_init_candidate(iVar1 + 0x60);
  hp1020_list_init_candidate(iVar1 + 0x68);
  *(undefined2 *)(iVar1 + 0x70) = 0;
  *(undefined4 *)(iVar1 + 0x84) = 0;
  *(undefined4 *)(iVar1 + 0x88) = 0;
  *(undefined4 *)(iVar1 + 0x8c) = 0;
  *(undefined1 *)(iVar1 + 0x90) = 0;
  *(undefined1 *)(iVar1 + 0x74) = 0;
  *(undefined1 *)(iVar1 + 0x77) = 0;
  hp1020_work_common_init_candidate(iVar1);
  return;
}
