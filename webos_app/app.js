'use strict';

const SUPABASE_URL = 'https://cdtxpefohpwtusmqengu.supabase.co';
// Public client value only; Supabase row-level security enforces authorization.
const SUPABASE_PUBLISHABLE_VALUE = 'sb_publishable_hp_c_ek7bYv33-fLqmgvnw_KS9T33Oi';
const PAGE_SIZE = 40;
const STORE_CATEGORIES = [
  'Business',
  'Culture',
  'Documentary',
  'Education',
  'Legislative',
  'News',
  'Science',
  'Weather'
];
const EXPLICIT_NAME_PATTERN = /\b(porn|porno|pornography|xxx|erotic|erotica|playboy|hustler|redlight)\b/i;
const STORAGE = {
  notice: 'tvviewer-webos-notice-v1',
  favorites: 'tvviewer-webos-favorites'
};

const state = {
  channels: [],
  total: 0,
  page: 0,
  view: 'all',
  favorites: new Set(),
  activeChannel: null,
  sourceIndex: 0,
  hls: null,
  loading: false,
  lastCatalogFocus: null
};

const elements = {};

document.addEventListener('DOMContentLoaded', initialize);

function initialize() {
  cacheElements();
  bindEvents();
  state.favorites = new Set(readJson(STORAGE.favorites, []));
  updateFavoriteCount();

  if (localStorage.getItem(STORAGE.notice) !== 'accepted') {
    openModal(elements.firstRunModal, elements.acceptNotice);
    return;
  }

  loadChannels();
}

function cacheElements() {
  [
    'connectionStatus', 'favoriteCount', 'searchInput', 'categorySelect',
    'typeSelect', 'applyFilters', 'clearFilters', 'catalogTitle',
    'catalogSummary', 'channelGrid', 'emptyState', 'previousPage',
    'nextPage', 'pageLabel', 'playerLayer', 'videoPlayer', 'playerTitle',
    'playerMeta', 'playerMessage', 'playPause', 'muteButton',
    'favoriteButton', 'sourceButton', 'closePlayer', 'firstRunModal',
    'acceptNotice', 'helpModal', 'openHelp', 'closeHelp', 'toast'
  ].forEach((id) => {
    elements[id] = document.getElementById(id);
  });
}

function bindEvents() {
  elements.acceptNotice.addEventListener('click', () => {
    localStorage.setItem(STORAGE.notice, 'accepted');
    closeModal(elements.firstRunModal);
    loadChannels();
  });

  elements.openHelp.addEventListener('click', () => openModal(elements.helpModal, elements.closeHelp));
  elements.closeHelp.addEventListener('click', () => closeModal(elements.helpModal));
  elements.applyFilters.addEventListener('click', () => {
    state.page = 0;
    loadChannels();
  });
  elements.clearFilters.addEventListener('click', clearFilters);
  elements.previousPage.addEventListener('click', () => changePage(-1));
  elements.nextPage.addEventListener('click', () => changePage(1));
  elements.searchInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      state.page = 0;
      loadChannels();
    }
  });

  document.querySelectorAll('[data-view]').forEach((button) => {
    button.addEventListener('click', () => setView(button.dataset.view));
  });

  elements.playPause.addEventListener('click', togglePlayback);
  elements.muteButton.addEventListener('click', toggleMute);
  elements.favoriteButton.addEventListener('click', toggleActiveFavorite);
  elements.sourceButton.addEventListener('click', playNextSource);
  elements.closePlayer.addEventListener('click', closePlayer);

  elements.videoPlayer.addEventListener('play', () => {
    elements.playPause.textContent = 'Pause';
    hidePlayerMessage();
  });
  elements.videoPlayer.addEventListener('pause', () => {
    elements.playPause.textContent = 'Play';
  });
  elements.videoPlayer.addEventListener('error', () => showPlayerMessage('This source could not be played. Try Next source.'));

  document.addEventListener('keydown', handleRemoteKey);
  document.addEventListener('wheel', handleWheel, { passive: false });
  window.addEventListener('offline', () => setConnection('Offline', true));
  window.addEventListener('online', () => {
    setConnection('Connected', false);
    if (!state.channels.length) loadChannels();
  });
}

async function loadChannels() {
  if (state.loading) return;
  state.loading = true;
  setConnection('Loading catalog...', false);
  elements.catalogSummary.textContent = 'Loading channels...';
  elements.channelGrid.innerHTML = renderSkeletons();
  elements.emptyState.classList.add('hidden');

  try {
    const result = state.view === 'favorites'
      ? await loadFavoriteChannels()
      : await fetchChannels();
    state.channels = result.channels;
    state.total = result.total;
    renderChannels();
    setConnection('Connected', false);
  } catch (error) {
    console.error('Catalog load failed', error);
    state.channels = [];
    state.total = 0;
    renderChannels();
    setConnection('Catalog unavailable', true);
    showToast('Could not load channels. Check the television network connection.');
  } finally {
    state.loading = false;
  }
}

async function fetchChannels() {
  const params = new URLSearchParams();
  params.set('select', 'url_hash,name,urls,category,country,logo,media_type,source');
  params.set('order', 'name.asc');
  params.set('limit', String(PAGE_SIZE));
  params.set('offset', String(state.page * PAGE_SIZE));
  params.set('name', 'neq.');

  const search = sanitizeFilter(elements.searchInput.value);
  if (search) params.set('name', `ilike.*${search}*`);
  params.set(
    'category',
    elements.categorySelect.value
      ? `eq.${elements.categorySelect.value}`
      : `in.(${STORE_CATEGORIES.join(',')})`
  );
  if (elements.typeSelect.value) params.set('media_type', `eq.${elements.typeSelect.value}`);

  const response = await requestCatalog(params);
  return {
    channels: (await response.json()).map(normalizeChannel).filter(isStoreEligible),
    total: parseTotal(response.headers.get('content-range'))
  };
}

async function loadFavoriteChannels() {
  const hashes = Array.from(state.favorites);
  if (!hashes.length) return { channels: [], total: 0 };

  const pageHashes = hashes.slice(state.page * PAGE_SIZE, (state.page + 1) * PAGE_SIZE);
  const params = new URLSearchParams();
  params.set('select', 'url_hash,name,urls,category,country,logo,media_type,source');
  params.set('url_hash', `in.(${pageHashes.join(',')})`);
  params.set('order', 'name.asc');
  params.set('limit', String(PAGE_SIZE));

  const response = await requestCatalog(params);
  return {
    channels: (await response.json()).map(normalizeChannel).filter(isStoreEligible),
    total: hashes.length
  };
}

function requestCatalog(params) {
  return fetch(`${SUPABASE_URL}/rest/v1/channels?${params.toString()}`, {
    headers: {
      apikey: SUPABASE_PUBLISHABLE_VALUE,
      Authorization: `Bearer ${SUPABASE_PUBLISHABLE_VALUE}`,
      Prefer: 'count=exact'
    }
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error((await response.text()) || `Catalog HTTP ${response.status}`);
    }
    return response;
  });
}

function normalizeChannel(channel) {
  const urls = Array.isArray(channel.urls)
    ? channel.urls.filter(isSafeMediaUrl)
    : [];
  return {
    url_hash: channel.url_hash || '',
    name: channel.name || 'Unknown channel',
    urls,
    category: channel.category || 'General',
    country: channel.country || 'Unknown',
    logo: isSafeMediaUrl(channel.logo) ? channel.logo : '',
    media_type: channel.media_type || 'TV',
    source: channel.source || 'Community'
  };
}

function isStoreEligible(channel) {
  return channel.urls.length > 0
    && STORE_CATEGORIES.includes(channel.category)
    && !EXPLICIT_NAME_PATTERN.test(channel.name);
}

function renderChannels() {
  elements.channelGrid.innerHTML = '';
  const isFavorites = state.view === 'favorites';
  const search = sanitizeFilter(elements.searchInput.value);
  const category = elements.categorySelect.value;
  elements.catalogTitle.textContent = isFavorites
    ? 'Favorite channels'
    : search
      ? `Results for "${search}"`
      : category
        ? `${category} channels`
        : 'Public-interest channels';
  elements.catalogSummary.textContent = state.total
    ? `${state.total.toLocaleString()} matching channel${state.total === 1 ? '' : 's'}`
    : 'No matching channels';
  elements.emptyState.classList.toggle('hidden', state.channels.length > 0);

  state.channels.forEach((channel) => {
    const card = document.createElement('button');
    card.type = 'button';
    card.className = 'channel-card focusable';
    card.dataset.hash = channel.url_hash;
    card.setAttribute('aria-label', `Play ${channel.name}`);
    card.innerHTML = `
      <span class="channel-art">
        ${channel.logo
          ? `<img src="${escapeAttribute(channel.logo)}" alt="" loading="lazy">`
          : `<span class="channel-monogram">${escapeHtml(channel.name.charAt(0).toUpperCase())}</span>`}
      </span>
      <span class="channel-info">
        <span class="channel-name">${escapeHtml(channel.name)}</span>
        <span class="channel-meta">${escapeHtml(channel.country)} · ${escapeHtml(channel.category)}</span>
      </span>
      ${state.favorites.has(channel.url_hash) ? '<span class="favorite-mark">★</span>' : ''}
    `;
    card.addEventListener('click', () => openPlayer(channel, card));
    elements.channelGrid.appendChild(card);
  });

  updatePagination();
  requestAnimationFrame(() => {
    const preferred = elements.channelGrid.querySelector(`[data-hash="${cssEscape(state.lastCatalogFocus || '')}"]`)
      || elements.channelGrid.querySelector('.channel-card');
    if (preferred) preferred.focus();
  });
}

function renderSkeletons() {
  return Array.from({ length: 10 }, () => (
    '<div class="channel-card"><span class="channel-art"></span><span class="channel-info"><span class="channel-name">Loading...</span></span></div>'
  )).join('');
}

function updatePagination() {
  const pages = Math.max(1, Math.ceil(state.total / PAGE_SIZE));
  elements.pageLabel.textContent = `Page ${state.page + 1} of ${pages}`;
  elements.previousPage.disabled = state.page === 0;
  elements.nextPage.disabled = state.page + 1 >= pages;
}

function changePage(delta) {
  const next = state.page + delta;
  const pages = Math.max(1, Math.ceil(state.total / PAGE_SIZE));
  if (next < 0 || next >= pages) return;
  state.page = next;
  loadChannels();
  window.scrollTo(0, 0);
}

function setView(view) {
  if (view !== 'all' && view !== 'favorites') return;
  state.view = view;
  state.page = 0;
  document.querySelectorAll('[data-view]').forEach((button) => {
    button.classList.toggle('active', button.dataset.view === view);
  });
  loadChannels();
}

function clearFilters() {
  elements.searchInput.value = '';
  elements.categorySelect.value = '';
  elements.typeSelect.value = '';
  state.page = 0;
  state.view = 'all';
  document.querySelectorAll('[data-view]').forEach((button) => {
    button.classList.toggle('active', button.dataset.view === 'all');
  });
  loadChannels();
}

async function openPlayer(channel, card) {
  state.lastCatalogFocus = card.dataset.hash;
  state.activeChannel = channel;
  state.sourceIndex = 0;
  elements.playerLayer.classList.remove('hidden');
  elements.playerTitle.textContent = channel.name;
  elements.playerMeta.textContent = `${channel.country} · ${channel.category} · ${channel.media_type}`;
  elements.sourceButton.disabled = channel.urls.length < 2;
  updateActiveFavoriteButton();
  elements.closePlayer.focus();
  await playSource(0);
}

async function playSource(index) {
  const channel = state.activeChannel;
  if (!channel || !channel.urls.length) return;
  state.sourceIndex = index % channel.urls.length;
  const url = channel.urls[state.sourceIndex];
  showPlayerMessage(`Opening source ${state.sourceIndex + 1} of ${channel.urls.length}...`);
  destroyHls();
  const video = elements.videoPlayer;
  video.pause();
  video.removeAttribute('src');
  video.load();

  try {
    if (isLikelyHls(url) && video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = url;
      await startVideo(video);
      return;
    }

    if (isLikelyHls(url) && window.Hls && window.Hls.isSupported()) {
      state.hls = new window.Hls({
        enableWorker: true,
        lowLatencyMode: false,
        manifestLoadingTimeOut: 15000,
        levelLoadingTimeOut: 15000
      });
      state.hls.loadSource(url);
      state.hls.attachMedia(video);
      state.hls.on(window.Hls.Events.MANIFEST_PARSED, () => startVideo(video));
      state.hls.on(window.Hls.Events.ERROR, (_event, data) => {
        if (data && data.fatal) showPlayerMessage('Stream failed. Select Next source or return to channels.');
      });
      return;
    }

    video.src = url;
    await startVideo(video);
  } catch (error) {
    console.error('Playback failed', error);
    showPlayerMessage('Stream failed. Select Next source or return to channels.');
  }
}

async function startVideo(video) {
  try {
    await video.play();
    hidePlayerMessage();
  } catch (error) {
    console.warn('Playback did not start automatically', error);
    showPlayerMessage('Press Play to start this stream.');
  }
}

function closePlayer() {
  destroyHls();
  elements.videoPlayer.pause();
  elements.videoPlayer.removeAttribute('src');
  elements.videoPlayer.load();
  elements.playerLayer.classList.add('hidden');
  state.activeChannel = null;
  renderChannels();
}

function togglePlayback() {
  if (elements.videoPlayer.paused) {
    startVideo(elements.videoPlayer);
  } else {
    elements.videoPlayer.pause();
  }
}

function toggleMute() {
  elements.videoPlayer.muted = !elements.videoPlayer.muted;
  elements.muteButton.textContent = elements.videoPlayer.muted ? 'Unmute' : 'Mute';
}

function playNextSource() {
  if (!state.activeChannel || state.activeChannel.urls.length < 2) return;
  playSource((state.sourceIndex + 1) % state.activeChannel.urls.length);
}

function toggleActiveFavorite() {
  if (!state.activeChannel) return;
  const hash = state.activeChannel.url_hash;
  if (state.favorites.has(hash)) {
    state.favorites.delete(hash);
    showToast('Removed from favorites');
  } else {
    state.favorites.add(hash);
    showToast('Added to favorites');
  }
  writeFavorites();
  updateActiveFavoriteButton();
}

function updateActiveFavoriteButton() {
  if (!state.activeChannel) return;
  elements.favoriteButton.textContent = state.favorites.has(state.activeChannel.url_hash)
    ? 'Remove favorite'
    : 'Add favorite';
}

function writeFavorites() {
  localStorage.setItem(STORAGE.favorites, JSON.stringify(Array.from(state.favorites)));
  updateFavoriteCount();
}

function updateFavoriteCount() {
  elements.favoriteCount.textContent = String(state.favorites.size);
}

function handleRemoteKey(event) {
  const keyCode = event.keyCode || event.which;
  if (event.key === 'Escape' || keyCode === 461 || keyCode === 10009) {
    event.preventDefault();
    handleBack();
    return;
  }

  if (!elements.playerLayer.classList.contains('hidden')) {
    if (event.key === 'MediaPlayPause' || keyCode === 415 || keyCode === 19) {
      event.preventDefault();
      togglePlayback();
      return;
    }
    if (keyCode === 413) {
      event.preventDefault();
      elements.videoPlayer.pause();
      return;
    }
  }

  const directions = {
    ArrowLeft: 'left',
    ArrowRight: 'right',
    ArrowUp: 'up',
    ArrowDown: 'down'
  };
  const direction = directions[event.key];
  if (!direction || isTextEntry(document.activeElement)) return;
  event.preventDefault();
  moveFocus(direction);
}

function handleBack() {
  if (!elements.firstRunModal.classList.contains('hidden')) {
    exitApp();
    return;
  }
  if (!elements.helpModal.classList.contains('hidden')) {
    closeModal(elements.helpModal);
    return;
  }
  if (!elements.playerLayer.classList.contains('hidden')) {
    closePlayer();
    return;
  }
  exitApp();
}

function exitApp() {
  if (window.webOS && typeof window.webOS.platformBack === 'function') {
    window.webOS.platformBack();
    return;
  }
  window.close();
}

function handleWheel(event) {
  if (!elements.firstRunModal.classList.contains('hidden')
    || !elements.helpModal.classList.contains('hidden')
    || !elements.playerLayer.classList.contains('hidden')
    || isTextEntry(event.target)
    || Math.abs(event.deltaY) < 1) {
    return;
  }
  event.preventDefault();
  window.scrollBy({ top: event.deltaY, behavior: 'auto' });
}

function moveFocus(direction) {
  const current = document.activeElement;
  const candidates = visibleFocusable().filter((element) => element !== current);
  if (!candidates.length) return;
  if (!current || !current.classList.contains('focusable')) {
    candidates[0].focus();
    return;
  }

  const origin = centerOf(current.getBoundingClientRect());
  const scored = candidates.map((element) => {
    const target = centerOf(element.getBoundingClientRect());
    const dx = target.x - origin.x;
    const dy = target.y - origin.y;
    if (!isInDirection(dx, dy, direction)) return null;
    const primary = direction === 'left' || direction === 'right' ? Math.abs(dx) : Math.abs(dy);
    const secondary = direction === 'left' || direction === 'right' ? Math.abs(dy) : Math.abs(dx);
    return { element, score: primary + secondary * 2.4 };
  }).filter(Boolean).sort((a, b) => a.score - b.score);

  if (scored[0]) {
    scored[0].element.focus();
    scored[0].element.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' });
  }
}

function visibleFocusable() {
  const scope = !elements.firstRunModal.classList.contains('hidden')
    ? elements.firstRunModal
    : !elements.helpModal.classList.contains('hidden')
      ? elements.helpModal
      : !elements.playerLayer.classList.contains('hidden')
        ? elements.playerLayer
        : document;
  return Array.from(scope.querySelectorAll('.focusable:not([disabled])')).filter((element) => {
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  });
}

function isInDirection(dx, dy, direction) {
  if (direction === 'left') return dx < -5;
  if (direction === 'right') return dx > 5;
  if (direction === 'up') return dy < -5;
  return dy > 5;
}

function centerOf(rect) {
  return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
}

function isTextEntry(element) {
  return element && (element.tagName === 'INPUT' || element.tagName === 'SELECT');
}

function openModal(modal, focusTarget) {
  modal.classList.remove('hidden');
  requestAnimationFrame(() => focusTarget.focus());
}

function closeModal(modal) {
  modal.classList.add('hidden');
  requestAnimationFrame(() => {
    const first = visibleFocusable()[0];
    if (first) first.focus();
  });
}

function setConnection(text, error) {
  elements.connectionStatus.textContent = text;
  elements.connectionStatus.classList.toggle('error', error);
}

function showPlayerMessage(message) {
  elements.playerMessage.textContent = message;
  elements.playerMessage.classList.remove('hidden');
}

function hidePlayerMessage() {
  elements.playerMessage.classList.add('hidden');
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.remove('hidden');
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => elements.toast.classList.add('hidden'), 3000);
}

function destroyHls() {
  if (state.hls) {
    state.hls.destroy();
    state.hls = null;
  }
}

function parseTotal(contentRange) {
  if (!contentRange || !contentRange.includes('/')) return 0;
  const value = Number(contentRange.split('/')[1]);
  return Number.isFinite(value) ? value : 0;
}

function sanitizeFilter(value) {
  return String(value || '').replace(/[,*:()]/g, ' ').replace(/\s+/g, ' ').trim();
}

function isSafeMediaUrl(value) {
  if (!value || typeof value !== 'string') return false;
  try {
    const url = new URL(value);
    return url.protocol === 'https:' || url.protocol === 'http:';
  } catch (_error) {
    return false;
  }
}

function isLikelyHls(url) {
  return /\.m3u8(?:$|[?#])/i.test(url) || url.toLowerCase().includes('m3u8');
}

function readJson(key, fallback) {
  try {
    const value = JSON.parse(localStorage.getItem(key) || '');
    return value || fallback;
  } catch (_error) {
    return fallback;
  }
}

function escapeHtml(value) {
  const node = document.createElement('span');
  node.textContent = String(value || '');
  return node.innerHTML;
}

function escapeAttribute(value) {
  return escapeHtml(value).replace(/"/g, '&quot;');
}

function cssEscape(value) {
  if (window.CSS && typeof window.CSS.escape === 'function') return window.CSS.escape(value);
  return String(value).replace(/[^a-zA-Z0-9_-]/g, '\\$&');
}
