const SUPABASE_URL = 'https://cdtxpefohpwtusmqengu.supabase.co';
const SUPABASE_KEY = 'sb_publishable_hp_c_ek7bYv33-fLqmgvnw_KS9T33Oi';
const CHANNELS_TABLE = 'channels';
const PAGE_SIZE = 200;
const FACET_BATCH_SIZE = 1000;
const STORAGE_KEYS = {
  favorites: 'tvViewerFavorites',
  sidebarCollapsed: 'tvViewerSidebarCollapsed'
};

const state = {
  channels: [],
  totalCount: 0,
  offset: 0,
  hasMore: true,
  loading: false,
  favorites: new Set(),
  view: 'all',
  filters: {
    search: '',
    category: '',
    country: '',
    mediaType: ''
  },
  activeChannel: null,
  hls: null,
  requestToken: 0,
  activeLoadToken: 0,
  facetCounts: {
    categories: new Map(),
    countries: new Map()
  },
  facetsLoaded: false,
  localSearchTerm: ''
};

const collator = new Intl.Collator(undefined, { sensitivity: 'base', numeric: true });
let searchTimer = null;
let loadObserver = null;

const elements = {};

document.addEventListener('DOMContentLoaded', () => {
  cacheElements();
  renderLoadingSkeleton();
  bindEvents();
  initialize().catch((error) => {
    console.error('TV Viewer initialization failed', error);
    setStatus('Unable to load channels from Supabase.', true);
    showToast('Could not initialize TV Viewer. Check your connection and reload.', true);
  });
});

function cacheElements() {
  Object.assign(elements, {
    appShell: document.getElementById('appShell'),
    searchInput: document.getElementById('searchInput'),
    clearSearch: document.getElementById('clearSearch'),
    refreshButton: document.getElementById('refreshButton'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    categorySelect: document.getElementById('categorySelect'),
    countrySelect: document.getElementById('countrySelect'),
    typeSelect: document.getElementById('typeSelect'),
    loadingGrid: document.getElementById('loadingGrid'),
    emptyState: document.getElementById('emptyState'),
    channelGrid: document.getElementById('channelGrid'),
    categoryList: document.getElementById('categoryList'),
    countryList: document.getElementById('countryList'),
    visibleCount: document.getElementById('visibleCount'),
    loadedCount: document.getElementById('loadedCount'),
    totalCount: document.getElementById('totalCount'),
    statusPill: document.getElementById('statusPill'),
    channelSummary: document.getElementById('channelSummary'),
    favoritesBadge: document.getElementById('favoritesBadge'),
    loadStatus: document.getElementById('loadStatus'),
    loadSentinel: document.getElementById('loadSentinel'),
    playerDock: document.getElementById('playerDock'),
    videoPlayer: document.getElementById('videoPlayer'),
    playerTitle: document.getElementById('playerTitle'),
    playerSubtitle: document.getElementById('playerSubtitle'),
    playerCategory: document.getElementById('playerCategory'),
    playerCountry: document.getElementById('playerCountry'),
    playerType: document.getElementById('playerType'),
    sourceSelect: document.getElementById('sourceSelect'),
    favoriteButton: document.getElementById('favoriteButton'),
    closePlayerButton: document.getElementById('closePlayerButton')
  });
}

async function initialize() {
  state.favorites = new Set(await storageGet(STORAGE_KEYS.favorites, []));
  const collapsed = await storageGet(STORAGE_KEYS.sidebarCollapsed, false);
  if (collapsed) {
    elements.appShell.classList.add('sidebar-collapsed');
  }

  updateFavoritesBadge();
  setupInfiniteScroll();
  setStatus('Connecting to Supabase…');
  await resetAndLoad();
  loadFacetCounts().catch((error) => {
    console.warn('Facet preload failed', error);
  });
}

function bindEvents() {
  elements.searchInput.addEventListener('input', handleSearchInput);
  elements.clearSearch.addEventListener('click', () => {
    elements.searchInput.value = '';
    handleSearchInput();
    elements.searchInput.focus();
  });
  elements.categorySelect.addEventListener('change', () => {
    state.filters.category = elements.categorySelect.value;
    syncSidebarFilters();
    resetAndLoad();
  });
  elements.countrySelect.addEventListener('change', () => {
    state.filters.country = elements.countrySelect.value;
    syncSidebarFilters();
    resetAndLoad();
  });
  elements.typeSelect.addEventListener('change', () => {
    state.filters.mediaType = elements.typeSelect.value;
    resetAndLoad();
  });
  elements.refreshButton.addEventListener('click', () => resetAndLoad(true));
  elements.sidebarToggle.addEventListener('click', toggleSidebar);
  elements.closePlayerButton.addEventListener('click', closePlayer);
  elements.favoriteButton.addEventListener('click', () => {
    if (state.activeChannel) {
      toggleFavorite(state.activeChannel.url_hash);
    }
  });
  elements.sourceSelect.addEventListener('change', () => {
    if (state.activeChannel) {
      loadStream(elements.sourceSelect.value);
    }
  });

  for (const button of document.querySelectorAll('[data-view]')) {
    button.addEventListener('click', () => setView(button.dataset.view || 'all'));
  }

  window.addEventListener('beforeunload', destroyHls);
}

function toggleSidebar() {
  const collapsed = elements.appShell.classList.toggle('sidebar-collapsed');
  storageSet(STORAGE_KEYS.sidebarCollapsed, collapsed);
}

function handleSearchInput() {
  const value = elements.searchInput.value.trim();
  state.filters.search = value;
  state.localSearchTerm = value.toLowerCase();
  elements.clearSearch.hidden = value.length === 0;
  renderChannels();

  if (searchTimer) {
    clearTimeout(searchTimer);
  }
  searchTimer = window.setTimeout(() => {
    resetAndLoad();
  }, 300);
}

function setView(view) {
  if (state.view === view) {
    return;
  }

  state.view = view;
  for (const button of document.querySelectorAll('[data-view]')) {
    button.classList.toggle('active', button.dataset.view === view);
  }
  resetAndLoad();
}

function setupInfiniteScroll() {
  loadObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting && state.hasMore && !state.loading) {
        loadChannels();
      }
    }
  }, {
    rootMargin: '400px 0px 400px 0px'
  });

  loadObserver.observe(elements.loadSentinel);
}

async function resetAndLoad(force = false) {
  state.requestToken += 1;
  state.loading = false;
  state.activeLoadToken = 0;
  state.offset = 0;
  state.totalCount = 0;
  state.hasMore = true;
  state.channels = [];
  renderLoadingSkeleton();
  renderChannels();
  updateCounts();
  if (force) {
    setStatus('Refreshing channel catalog…');
  }
  await loadChannels({ reset: true });
}

async function loadChannels({ reset = false } = {}) {
  if (state.loading) {
    return;
  }

  const token = state.requestToken;
  const favoriteIds = Array.from(state.favorites);
  if (state.view === 'favorites' && favoriteIds.length === 0) {
    state.channels = [];
    state.totalCount = 0;
    state.offset = 0;
    state.hasMore = false;
    renderChannels();
    updateCounts();
    elements.loadingGrid.classList.add('hidden');
    setStatus('No favorites saved yet.');
    return;
  }

  state.loading = true;
  state.activeLoadToken = token;
  elements.loadStatus.textContent = state.offset === 0 ? 'Loading channels…' : 'Loading more channels…';

  try {
    const result = await fetchChannels(state.offset, PAGE_SIZE, state.filters, state.view, favoriteIds);
    if (token !== state.requestToken) {
      return;
    }

    const fetchedChannels = result.data
      .map(normalizeChannel)
      .filter((channel) => channel.url);

    if (reset) {
      state.channels = fetchedChannels;
    } else {
      const existing = new Set(state.channels.map((channel) => channel.url_hash));
      for (const channel of fetchedChannels) {
        if (!existing.has(channel.url_hash)) {
          state.channels.push(channel);
          existing.add(channel.url_hash);
        }
      }
    }

    state.totalCount = result.totalCount;
    state.offset += fetchedChannels.length;
    state.hasMore = state.channels.length < state.totalCount && fetchedChannels.length > 0;

    renderChannels();
    updateCounts();
    elements.loadingGrid.classList.add('hidden');
    syncFacetOptions();

    if (state.totalCount > 0) {
      setStatus(`Connected to Supabase • ${state.totalCount.toLocaleString()} channels`, false, true);
    } else {
      setStatus('No channels returned for the current filters.');
    }

    elements.loadStatus.textContent = state.hasMore
      ? `Loaded ${state.channels.length.toLocaleString()} of ${state.totalCount.toLocaleString()} channels. Scroll to continue.`
      : `Loaded ${state.channels.length.toLocaleString()} channels.`;
  } catch (error) {
    console.error('Failed to load channels', error);
    if (token === state.requestToken) {
      elements.loadingGrid.classList.add('hidden');
      renderChannels();
      setStatus('Supabase request failed.', true);
      elements.loadStatus.textContent = 'Unable to load channels.';
      showToast(error.message || 'Failed to fetch channels.', true);
    }
  } finally {
    if (state.activeLoadToken === token) {
      state.loading = false;
    }
  }
}

async function fetchChannels(offset, limit, filters, view, favoriteIds) {
  const params = new URLSearchParams();
  params.set('select', 'url_hash,name,urls,category,country,logo,media_type,source');
  params.set('order', 'name.asc');
  params.set('limit', String(limit));
  params.set('offset', String(offset));

  if (filters.category) {
    params.set('category', `eq.${filters.category}`);
  }
  if (filters.country) {
    params.set('country', `eq.${filters.country}`);
  }
  if (filters.mediaType) {
    params.set('media_type', `eq.${filters.mediaType}`);
  }
  if (filters.search) {
    const safeSearch = sanitizeSearch(filters.search);
    if (safeSearch) {
      params.set('name', `ilike.*${safeSearch}*`);
    }
  }
  if (view === 'favorites') {
    params.set('url_hash', `in.(${favoriteIds.join(',')})`);
  }

  const response = await fetch(`${SUPABASE_URL}/rest/v1/${CHANNELS_TABLE}?${params.toString()}`, {
    headers: {
      apikey: SUPABASE_KEY,
      Authorization: `Bearer ${SUPABASE_KEY}`,
      Prefer: 'count=exact'
    }
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HTTP ${response.status}`);
  }

  const data = await response.json();
  const contentRange = response.headers.get('content-range') || '0-0/0';
  const totalCount = Number(contentRange.split('/')[1] || 0);
  return { data, totalCount };
}

function sanitizeSearch(value) {
  return value.replace(/[,*:()]/g, ' ').replace(/\s+/g, ' ').trim();
}

function normalizeChannel(channel) {
  const urls = Array.isArray(channel.urls) ? channel.urls.filter(Boolean) : [];
  return {
    url_hash: channel.url_hash,
    name: channel.name || 'Unknown Channel',
    category: channel.category || 'General',
    country: channel.country || 'Unknown',
    media_type: channel.media_type || 'TV',
    source: channel.source || 'Community',
    logo: channel.logo || '',
    urls,
    url: urls[0] || ''
  };
}

function renderLoadingSkeleton() {
  elements.loadingGrid.innerHTML = '';
  for (let index = 0; index < 8; index += 1) {
    const card = document.createElement('div');
    card.className = 'skeleton-card';
    elements.loadingGrid.appendChild(card);
  }
  elements.loadingGrid.classList.toggle('hidden', state.channels.length > 0);
}

function renderChannels() {
  const visibleChannels = getVisibleChannels();
  elements.channelGrid.innerHTML = '';

  if (visibleChannels.length === 0) {
    const showEmptyState = elements.loadingGrid.classList.contains('hidden') && !state.loading;
    elements.emptyState.classList.toggle('hidden', !showEmptyState);
    updateCounts(0);
    return;
  }

  elements.emptyState.classList.add('hidden');
  const fragment = document.createDocumentFragment();
  for (const channel of visibleChannels) {
    fragment.appendChild(createChannelCard(channel));
  }
  elements.channelGrid.appendChild(fragment);
  updateCounts(visibleChannels.length);
}

function getVisibleChannels() {
  const searchTerm = state.localSearchTerm;
  return state.channels.filter((channel) => {
    if (!searchTerm) {
      return true;
    }
    const haystack = `${channel.name} ${channel.country} ${channel.category}`.toLowerCase();
    return haystack.includes(searchTerm);
  });
}

function createChannelCard(channel) {
  const card = document.createElement('article');
  card.className = 'channel-card';
  if (state.activeChannel && state.activeChannel.url_hash === channel.url_hash) {
    card.classList.add('is-playing');
  }

  const header = document.createElement('div');
  header.className = 'channel-header';

  const logo = document.createElement('div');
  logo.className = 'channel-logo';
  if (channel.logo) {
    const image = document.createElement('img');
    image.loading = 'lazy';
    image.src = channel.logo;
    image.alt = `${channel.name} logo`;
    image.referrerPolicy = 'no-referrer';
    image.addEventListener('error', () => {
      image.remove();
      logo.textContent = getChannelMonogram(channel.name);
    }, { once: true });
    logo.appendChild(image);
  } else {
    logo.textContent = getChannelMonogram(channel.name);
  }

  const titleWrap = document.createElement('div');
  titleWrap.className = 'channel-title';

  const title = document.createElement('h3');
  title.className = 'channel-name';
  title.textContent = channel.name;

  const source = document.createElement('div');
  source.className = 'channel-source';
  source.textContent = `${channel.country} • ${channel.source}`;

  titleWrap.append(title, source);
  header.append(logo, titleWrap);

  const meta = document.createElement('div');
  meta.className = 'channel-meta';
  meta.append(
    createMetaPill(channel.category, 'category'),
    createMetaPill(channel.country, 'country'),
    createMetaPill(channel.media_type, channel.media_type === 'Radio' ? 'type-radio' : 'type-tv'),
    createMetaPill(`${channel.urls.length} source${channel.urls.length === 1 ? '' : 's'}`, 'sources')
  );

  const actions = document.createElement('div');
  actions.className = 'channel-actions';

  const playButton = document.createElement('button');
  playButton.className = 'primary-button';
  playButton.type = 'button';
  playButton.textContent = 'Play';
  playButton.addEventListener('click', () => playChannel(channel));

  const favoriteButton = document.createElement('button');
  favoriteButton.className = `secondary-button${state.favorites.has(channel.url_hash) ? ' favorite-active' : ''}`;
  favoriteButton.type = 'button';
  favoriteButton.textContent = state.favorites.has(channel.url_hash) ? '★ Saved' : '☆ Favorite';
  favoriteButton.addEventListener('click', () => toggleFavorite(channel.url_hash));

  actions.append(playButton, favoriteButton);
  card.append(header, meta, actions);
  return card;
}

function createMetaPill(text, extraClass) {
  const pill = document.createElement('span');
  pill.className = `meta-pill ${extraClass || ''}`.trim();
  pill.textContent = text;
  return pill;
}

function getChannelMonogram(name) {
  const clean = (name || '?').trim();
  return clean.slice(0, 1).toUpperCase();
}

async function toggleFavorite(urlHash) {
  if (state.favorites.has(urlHash)) {
    state.favorites.delete(urlHash);
  } else {
    state.favorites.add(urlHash);
  }

  await storageSet(STORAGE_KEYS.favorites, Array.from(state.favorites));
  updateFavoritesBadge();
  updatePlayerFavoriteState();

  if (state.view === 'favorites') {
    resetAndLoad();
    return;
  }

  renderChannels();
}

function updateFavoritesBadge() {
  elements.favoritesBadge.textContent = state.favorites.size.toLocaleString();
}

async function playChannel(channel) {
  state.activeChannel = channel;
  elements.playerDock.classList.remove('hidden');
  elements.playerTitle.textContent = channel.name;
  elements.playerSubtitle.textContent = `${channel.country} • ${channel.source} • ${channel.urls.length} available source${channel.urls.length === 1 ? '' : 's'}`;
  elements.playerCategory.textContent = channel.category;
  elements.playerCountry.textContent = channel.country;
  elements.playerType.textContent = channel.media_type;
  elements.sourceSelect.innerHTML = '';

  channel.urls.forEach((url, index) => {
    const option = document.createElement('option');
    option.value = url;
    option.textContent = channel.urls.length === 1 ? 'Primary stream' : `Source ${index + 1}`;
    elements.sourceSelect.appendChild(option);
  });

  updatePlayerFavoriteState();
  renderChannels();
  await loadStream(channel.url);
  elements.playerDock.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function updatePlayerFavoriteState() {
  if (!state.activeChannel) {
    return;
  }
  const isFavorite = state.favorites.has(state.activeChannel.url_hash);
  elements.favoriteButton.textContent = isFavorite ? '★ Saved favorite' : '☆ Save favorite';
  elements.favoriteButton.classList.toggle('favorite-active', isFavorite);
}

async function loadStream(url) {
  destroyHls();
  const video = elements.videoPlayer;
  video.pause();
  video.removeAttribute('src');
  video.load();

  try {
    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = url;
      await video.play();
      return;
    }

    if (window.Hls && window.Hls.isSupported()) {
      state.hls = new window.Hls({
        enableWorker: true,
        lowLatencyMode: true
      });
      state.hls.loadSource(url);
      state.hls.attachMedia(video);
      state.hls.on(window.Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch((error) => {
          console.warn('Autoplay blocked', error);
        });
      });
      state.hls.on(window.Hls.Events.ERROR, (_event, data) => {
        if (data && data.fatal) {
          showToast('Stream error. Try another source if available.', true);
        }
      });
      return;
    }

    video.src = url;
    await video.play();
  } catch (error) {
    console.error('Playback failed', error);
    showToast('Could not start playback for this channel.', true);
  }
}

function closePlayer() {
  destroyHls();
  elements.videoPlayer.pause();
  elements.videoPlayer.removeAttribute('src');
  elements.videoPlayer.load();
  elements.playerDock.classList.add('hidden');
  state.activeChannel = null;
  renderChannels();
}

function destroyHls() {
  if (state.hls) {
    state.hls.destroy();
    state.hls = null;
  }
}

async function loadFacetCounts() {
  const categories = new Map();
  const countries = new Map();
  let offset = 0;

  while (true) {
    const params = new URLSearchParams();
    params.set('select', 'category,country');
    params.set('limit', String(FACET_BATCH_SIZE));
    params.set('offset', String(offset));
    params.set('order', 'name.asc');

    const response = await fetch(`${SUPABASE_URL}/rest/v1/${CHANNELS_TABLE}?${params.toString()}`, {
      headers: {
        apikey: SUPABASE_KEY,
        Authorization: `Bearer ${SUPABASE_KEY}`
      }
    });

    if (!response.ok) {
      throw new Error(`Facet preload failed: ${response.status}`);
    }

    const rows = await response.json();
    if (!rows.length) {
      break;
    }

    for (const row of rows) {
      accumulateCount(categories, row.category || 'General');
      accumulateCount(countries, row.country || 'Unknown');
    }

    offset += rows.length;
    if (offset === rows.length || offset % (FACET_BATCH_SIZE * 2) === 0) {
      state.facetCounts.categories = categories;
      state.facetCounts.countries = countries;
      syncFacetOptions();
    }

    if (rows.length < FACET_BATCH_SIZE) {
      break;
    }
  }

  state.facetCounts.categories = categories;
  state.facetCounts.countries = countries;
  state.facetsLoaded = true;
  syncFacetOptions();
}

function accumulateCount(map, key) {
  map.set(key, (map.get(key) || 0) + 1);
}

function syncFacetOptions() {
  const categoryMap = state.facetsLoaded && state.facetCounts.categories.size
    ? state.facetCounts.categories
    : buildLocalFacetMap('category');
  const countryMap = state.facetsLoaded && state.facetCounts.countries.size
    ? state.facetCounts.countries
    : buildLocalFacetMap('country');

  populateSelect(elements.categorySelect, categoryMap, 'All categories', state.filters.category);
  populateSelect(elements.countrySelect, countryMap, 'All countries', state.filters.country);
  populateSidebarList(elements.categoryList, categoryMap, state.filters.category, 'category');
  populateSidebarList(elements.countryList, countryMap, state.filters.country, 'country');
}

function buildLocalFacetMap(field) {
  const map = new Map();
  for (const channel of state.channels) {
    const key = channel[field] || (field === 'category' ? 'General' : 'Unknown');
    accumulateCount(map, key);
  }
  return map;
}

function populateSelect(select, valuesMap, placeholder, selectedValue) {
  const values = sortFacetEntries(valuesMap);
  select.innerHTML = '';

  const placeholderOption = document.createElement('option');
  placeholderOption.value = '';
  placeholderOption.textContent = placeholder;
  select.appendChild(placeholderOption);

  for (const [value, count] of values) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = `${value} (${count.toLocaleString()})`;
    if (value === selectedValue) {
      option.selected = true;
    }
    select.appendChild(option);
  }
}

function populateSidebarList(container, valuesMap, selectedValue, type) {
  const values = sortFacetEntries(valuesMap);
  container.innerHTML = '';

  const allButton = document.createElement('button');
  allButton.type = 'button';
  allButton.className = `sidebar-item${selectedValue ? '' : ' active'}`;
  allButton.innerHTML = `<span class="sidebar-item-label">All</span><span class="sidebar-item-count">${sumFacetCounts(valuesMap).toLocaleString()}</span>`;
  allButton.addEventListener('click', () => applySidebarFilter(type, ''));
  container.appendChild(allButton);

  for (const [value, count] of values) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `sidebar-item${value === selectedValue ? ' active' : ''}`;
    button.innerHTML = `<span class="sidebar-item-label">${escapeHtml(value)}</span><span class="sidebar-item-count">${count.toLocaleString()}</span>`;
    button.addEventListener('click', () => applySidebarFilter(type, value));
    container.appendChild(button);
  }
}

function sumFacetCounts(map) {
  let total = 0;
  for (const count of map.values()) {
    total += count;
  }
  return total;
}

function applySidebarFilter(type, value) {
  if (type === 'category') {
    state.filters.category = value;
    elements.categorySelect.value = value;
  }
  if (type === 'country') {
    state.filters.country = value;
    elements.countrySelect.value = value;
  }
  syncSidebarFilters();
  resetAndLoad();
}

function syncSidebarFilters() {
  populateSidebarList(
    elements.categoryList,
    state.facetsLoaded ? state.facetCounts.categories : buildLocalFacetMap('category'),
    state.filters.category,
    'category'
  );
  populateSidebarList(
    elements.countryList,
    state.facetsLoaded ? state.facetCounts.countries : buildLocalFacetMap('country'),
    state.filters.country,
    'country'
  );
}

function sortFacetEntries(map) {
  return Array.from(map.entries()).sort((left, right) => {
    if (right[1] !== left[1]) {
      return right[1] - left[1];
    }
    return collator.compare(left[0], right[0]);
  });
}

function updateCounts(visibleCount = getVisibleChannels().length) {
  elements.visibleCount.textContent = visibleCount.toLocaleString();
  elements.loadedCount.textContent = state.channels.length.toLocaleString();
  elements.totalCount.textContent = state.totalCount.toLocaleString();
  elements.channelSummary.textContent = state.totalCount
    ? `Showing ${visibleCount.toLocaleString()} currently visible items from ${state.channels.length.toLocaleString()} loaded channels.`
    : 'No channels loaded yet.';
}

function setStatus(message, isError = false, ready = false) {
  elements.statusPill.textContent = message;
  elements.statusPill.classList.toggle('error', isError);
  elements.statusPill.classList.toggle('ready', ready && !isError);
}

function showToast(message, isError = false) {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = 'status-pill';
    toast.style.position = 'fixed';
    toast.style.right = '24px';
    toast.style.bottom = '24px';
    toast.style.zIndex = '200';
    toast.style.maxWidth = '360px';
    toast.style.boxShadow = '0 10px 24px rgba(0,0,0,0.28)';
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.classList.toggle('error', isError);
  toast.classList.add('ready');
  toast.hidden = false;

  clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    toast.hidden = true;
  }, 3200);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function storageGet(key, fallbackValue) {
  if (globalThis.chrome?.storage?.local) {
    return new Promise((resolve) => {
      chrome.storage.local.get({ [key]: fallbackValue }, (result) => {
        resolve(result[key]);
      });
    });
  }

  const raw = localStorage.getItem(key);
  return Promise.resolve(raw ? JSON.parse(raw) : fallbackValue);
}

function storageSet(key, value) {
  if (globalThis.chrome?.storage?.local) {
    return new Promise((resolve) => {
      chrome.storage.local.set({ [key]: value }, resolve);
    });
  }

  localStorage.setItem(key, JSON.stringify(value));
  return Promise.resolve();
}
