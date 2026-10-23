(() => {
  const openButton = document.getElementById('register-camera-open');
  if (!openButton) return;

  const panel = document.getElementById('register-camera-panel');
  const video = document.getElementById('register-camera-video');
  const captureButton = document.getElementById('register-camera-capture');
  const cancelButton = document.getElementById('register-camera-cancel');
  const status = document.getElementById('register-camera-status');
  const input = openButton.closest('form').querySelector('input[name="profile_picture"]');
  let stream = null;
  let requestId = 0;

  function closeCamera(restoreFocus = false) {
    requestId += 1;
    if (stream) stream.getTracks().forEach(track => track.stop());
    stream = null;
    video.srcObject = null;
    panel.hidden = true;
    captureButton.disabled = true;
    openButton.disabled = false;
    openButton.setAttribute('aria-expanded', 'false');
    if (restoreFocus) openButton.focus();
  }

  openButton.addEventListener('click', async () => {
    status.textContent = '';
    if (!navigator.mediaDevices?.getUserMedia || !window.isSecureContext) {
      status.textContent = 'Camera access needs HTTPS or localhost and a supported browser. You can still use Choose File.';
      return;
    }

    const currentRequest = ++requestId;
    openButton.disabled = true;
    panel.hidden = false;
    openButton.setAttribute('aria-expanded', 'true');
    status.textContent = 'Allow camera access in your browser to take a photo.';
    cancelButton.focus();
    try {
      const camera = await navigator.mediaDevices.getUserMedia({
        video: {facingMode: 'user', width: {ideal: 1280}, height: {ideal: 960}},
        audio: false,
      });
      // Cancel/navigation may happen while the permission prompt is open.
      if (currentRequest !== requestId) {
        camera.getTracks().forEach(track => track.stop());
        return;
      }
      stream = camera;
      video.srcObject = stream;
      await video.play();
      if (currentRequest !== requestId) return;
      captureButton.disabled = !video.videoWidth;
      status.textContent = 'Position yourself in the preview, then select Use photo.';
      captureButton.focus();
    } catch (error) {
      if (currentRequest !== requestId) return;
      closeCamera(true);
      status.textContent = error.name === 'NotAllowedError'
        ? 'Camera permission was denied. Allow it in your browser settings or use Choose File.'
        : 'The camera is unavailable or in use. Try again or use Choose File.';
    }
  });

  video.addEventListener('loadeddata', () => {
    captureButton.disabled = !stream || !video.videoWidth;
  });

  captureButton.addEventListener('click', () => {
    if (!stream || !video.videoWidth || captureButton.disabled) return;
    const currentRequest = requestId;
    captureButton.disabled = true;
    const canvas = document.createElement('canvas');
    const scale = Math.min(1, 1280 / Math.max(video.videoWidth, video.videoHeight));
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => {
      if (currentRequest !== requestId) return;
      try {
        if (!blob) throw new Error('Photo capture failed');
        const files = new DataTransfer();
        files.items.add(new File([blob], 'profile-camera.jpg', {type: 'image/jpeg'}));
        input.files = files.files;
        input.dispatchEvent(new Event('change', {bubbles: true}));
        closeCamera(true);
        status.textContent = 'Photo selected. It will upload when you create your account. Select Take photo again to retake it.';
      } catch {
        closeCamera(true);
        status.textContent = 'This browser could not attach the photo. Please use Choose File.';
      }
    }, 'image/jpeg', 0.9);
  });

  cancelButton.addEventListener('click', () => {
    closeCamera(true);
    status.textContent = 'Camera closed. Your previously selected photo is unchanged.';
  });
  panel.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      event.preventDefault();
      cancelButton.click();
    }
  });
  input.addEventListener('change', () => {
    closeCamera();
    status.textContent = '';
  });
  input.form.addEventListener('submit', () => closeCamera());
  window.addEventListener('pagehide', () => closeCamera());
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) closeCamera();
  });
})();
