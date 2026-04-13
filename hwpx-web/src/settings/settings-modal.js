import { hasKey, loadKey, saveKey, deleteKey } from './key-store.js';

export function initSettingsModal() {
  const modal = document.getElementById('settings-modal');
  const btnSettings = document.getElementById('btn-settings');
  const btnClose = document.querySelector('.btn-close-modal');
  const tabs = document.querySelectorAll('.tab');
  const tabContents = document.querySelectorAll('.tab-content');
  const btnSave = document.getElementById('btn-save-key');
  const btnDelete = document.getElementById('btn-delete-key');
  const selectModel = document.getElementById('ai-model-select');
  const aiStatus = document.getElementById('ai-status');

  let currentTab = 'gemini';

  function updateStatus() {
    const model = selectModel.value;
    if (hasKey(model)) {
      aiStatus.className = 'status-badge connected';
      aiStatus.title = "API Key 설정됨";
    } else {
      aiStatus.className = 'status-badge disconnected';
      aiStatus.title = "API Key 설정 필요";
    }
  }

  function loadCurrentKey() {
    const key = loadKey(currentTab);
    const input = document.getElementById(`input-api-${currentTab}`);
    if (input) input.value = key;
  }

  btnSettings.addEventListener('click', () => {
    currentTab = selectModel.value;
    // Activate appropriate tab
    tabs.forEach(t => t.classList.remove('active'));
    tabContents.forEach(c => c.style.display = 'none');
    
    document.querySelector(`.tab[data-target="tab-${currentTab}"]`).classList.add('active');
    document.getElementById(`tab-${currentTab}`).style.display = 'block';
    
    loadCurrentKey();
    modal.classList.add('active');
  });

  btnClose.addEventListener('click', () => modal.classList.remove('active'));

  tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      tabs.forEach(t => t.classList.remove('active'));
      tabContents.forEach(c => c.style.display = 'none');
      
      e.target.classList.add('active');
      const targetId = e.target.getAttribute('data-target');
      document.getElementById(targetId).style.display = 'block';
      currentTab = targetId.replace('tab-', '');
      loadCurrentKey();
    });
  });

  btnSave.addEventListener('click', () => {
    const input = document.getElementById(`input-api-${currentTab}`);
    if (input && input.value) {
      saveKey(currentTab, input.value);
      alert(`${currentTab} API Key가 저장되었습니다.`);
      updateStatus();
    }
  });

  btnDelete.addEventListener('click', () => {
    deleteKey(currentTab);
    const input = document.getElementById(`input-api-${currentTab}`);
    if (input) input.value = "";
    alert(`${currentTab} API Key가 삭제되었습니다.`);
    updateStatus();
  });

  selectModel.addEventListener('change', updateStatus);

  // Initial status
  updateStatus();
}
