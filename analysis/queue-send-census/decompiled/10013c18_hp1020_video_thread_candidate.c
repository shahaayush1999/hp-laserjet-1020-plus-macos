/* Function: 10013c18 hp1020_video_thread_candidate */


/* high confidence: Video Queue consumer */

void hp1020_video_thread_candidate(void)

{
  undefined *puVar1;
  uint *puVar2;
  int *piVar3;
  undefined4 uVar4;
  int iVar5;
  uint uVar6;
  int aiStack_30 [3];
  undefined4 uStack_24;

  puVar2 = DAT_10006768;
  puVar1 = PTR_DAT_10006764;
  PTR_DAT_10006764[0xbf] = 0x55;
  puVar1[0xf7] = 0x55;
  puVar1[0xe0] = 0xaa;
  memw();
  memw();
  *puVar2 = *puVar2 | 8;
  uVar6 = 0;
  FUN_1001214c();
  puVar1 = hp1020_video_state_ptr_word;
  do {
    while( true ) {
      while( true ) {
        uVar6 = uVar6 & 0xffffcfff;
        threadx_queue_receive_wait_candidate
                  (hp1020_video_queue_object_ptr_word,aiStack_30,0xffffffff);
        if (aiStack_30[0] == 0xb) break;
        if (aiStack_30[0] == 0xf) {
          uVar4 = rsil(1);
          uVar6 = uVar6 & 0xffffcfff;
          FUN_100171b0(0x13);
          uVar6 = uVar6 & 0xffffcfff;
          FUN_100171b0(10);
          uVar6 = uVar6 & 0xffffcfff;
          FUN_100171b0(0xb);
          uVar6 = uVar6 & 0xffffcfff;
          hp1020_video_reset_or_flush_candidate();
          *(undefined4 *)(puVar1 + 0x60) = 0;
          *(undefined4 *)(puVar1 + 100) = 0;
          wsr((char)uVar6,uVar4);
          rsync();
        }
      }
      if (*(int *)(puVar1 + 0x60) != 0) break;
      *(undefined4 *)(puVar1 + 0x60) = uStack_24;
LAB_10013c7d:
      piVar3 = *(int **)(puVar1 + 0x60);
      if (*piVar3 != 7) {
        iVar5 = *(int *)(*(int *)(piVar3[0x14] + 0xc) + 0x50);
        *(undefined4 *)PTR_DAT_10006774 = 0;
        if (iVar5 == 0) {
          uVar6 = uVar6 & 0xffffcfff;
          hp1020_video_prepare_page_candidate(piVar3);
          uVar6 = uVar6 & 0xffffcfff;
          hp1020_video_render_or_dma_candidate(piVar3);
        }
        else if (iVar5 - 1U < 2) {
          uVar6 = uVar6 & 0xffffcfff;
          hp1020_video_prepare_page_candidate(piVar3);
          uVar6 = uVar6 & 0xffffcfff;
          hp1020_video_alt_render_candidate(piVar3);
        }
      }
      aiStack_30[0] = 0x10;
      uVar6 = uVar6 & 0xffffcfff;
      hp1020_queue_send_candidate(1,aiStack_30);
    }
    if (*(int *)(puVar1 + 100) != 0) goto LAB_10013c7d;
    *(undefined4 *)(puVar1 + 100) = uStack_24;
  } while( true );
}
