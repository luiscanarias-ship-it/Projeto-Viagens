import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X, Save, MapPin, Target, FileText, Eye, Heart, Sparkles,
  BookOpen, Settings, Mail, CheckCircle, AlertCircle, Loader2, Image, CloudOff, Cloud
} from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TABS = [
  { id: 'basico', label: 'Basico', icon: MapPin },
  { id: 'conteudo', label: 'Conteudo', icon: FileText },
  { id: 'storytelling', label: 'Storytelling', icon: BookOpen },
  { id: 'config', label: 'Configuracoes', icon: Settings },
];

const REQUIRED_FIELDS = ['name', 'goal_amount'];
const AUTOSAVE_DELAY = 2000;

const getAutosaveKey = (journeyId) => `autosave_journey_${journeyId}`;

const JourneyEditForm = ({ journey, onSave, onCancel, getAuthHeaders, token, onEmailPreview }) => {
  const [form, setForm] = useState({ ...journey });
  const [tab, setTab] = useState('basico');
  const [saving, setSaving] = useState(false);
  const [generatingDescs, setGeneratingDescs] = useState(false);
  const [generatingStory, setGeneratingStory] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [errors, setErrors] = useState({});
  const [autosaveStatus, setAutosaveStatus] = useState(null);
  const [showRestoreBanner, setShowRestoreBanner] = useState(false);
  const [draftSource, setDraftSource] = useState(null); // 'server' or 'local'
  const autosaveTimer = useRef(null);
  const serverSaveTimer = useRef(null);
  const initialLoadDone = useRef(false);

  const originalJson = useMemo(() => JSON.stringify(journey), [journey]);
  const hasChanges = JSON.stringify(form) !== originalJson;

  // Load draft: try server first, then localStorage
  useEffect(() => {
    if (initialLoadDone.current) return;
    initialLoadDone.current = true;

    const loadDraft = async () => {
      // Try server draft first
      try {
        const res = await axios.get(`${API}/admin/drafts/journey_edit/${journey.journey_id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.data?.data) {
          setForm(prev => ({ ...journey, ...res.data.data }));
          setShowRestoreBanner(true);
          setDraftSource('server');
          return;
        }
      } catch { /* 404 = no server draft */ }

      // Fallback to localStorage
      try {
        const raw = localStorage.getItem(getAutosaveKey(journey.journey_id));
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed._autosave_ts && Date.now() - parsed._autosave_ts < 86400000) {
            const { _autosave_ts, ...data } = parsed;
            setForm(prev => ({ ...journey, ...data }));
            setShowRestoreBanner(true);
            setDraftSource('local');
            return;
          }
          localStorage.removeItem(getAutosaveKey(journey.journey_id));
        }
      } catch { /* ignore */ }
    };

    loadDraft();
  }, [journey, token]);

  // Autosave to localStorage + server with debounce
  useEffect(() => {
    if (!hasChanges) return;
    if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
    autosaveTimer.current = setTimeout(() => {
      // Save to localStorage (instant backup)
      try {
        localStorage.setItem(
          getAutosaveKey(journey.journey_id),
          JSON.stringify({ ...form, _autosave_ts: Date.now() })
        );
      } catch { /* storage full */ }

      // Save to server (async, non-blocking)
      if (serverSaveTimer.current) clearTimeout(serverSaveTimer.current);
      serverSaveTimer.current = setTimeout(async () => {
        try {
          await axios.put(`${API}/admin/drafts/journey_edit/${journey.journey_id}`, 
            { data: form },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          setAutosaveStatus('saved');
          setTimeout(() => setAutosaveStatus(null), 3000);
        } catch {
          // Server save failed, localStorage is still there
          setAutosaveStatus('saved-local');
          setTimeout(() => setAutosaveStatus(null), 3000);
        }
      }, 500);
    }, AUTOSAVE_DELAY);
    return () => {
      if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
      if (serverSaveTimer.current) clearTimeout(serverSaveTimer.current);
    };
  }, [form, hasChanges, journey.journey_id, token]);

  // Warn before leaving with unsaved changes
  useEffect(() => {
    const handler = (e) => {
      if (hasChanges) { e.preventDefault(); e.returnValue = ''; }
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [hasChanges]);

  const clearAutosave = useCallback(async () => {
    localStorage.removeItem(getAutosaveKey(journey.journey_id));
    try {
      await axios.delete(`${API}/admin/drafts/journey_edit/${journey.journey_id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch { /* ignore */ }
  }, [journey.journey_id, token]);

  const discardRestore = () => {
    setForm({ ...journey });
    clearAutosave();
    setShowRestoreBanner(false);
    setAutosaveStatus(null);
    setDraftSource(null);
  };

  const update = useCallback((field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors(prev => { const n = { ...prev }; delete n[field]; return n; });
  }, [errors]);

  const validate = () => {
    const e = {};
    if (!form.name?.trim()) e.name = 'Nome do destino e obrigatorio';
    if (!form.goal_amount || form.goal_amount < 100) e.goal_amount = 'Objetivo minimo: 100€';
    if (form.image_url && !form.image_url.startsWith('http')) e.image_url = 'URL invalido';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) {
      const firstErrorTab = errors.name || errors.goal_amount ? 'basico' : errors.image_url ? 'basico' : tab;
      setTab(firstErrorTab);
      return;
    }
    setSaving(true);
    try {
      await onSave(form);
      clearAutosave();
      setAutosaveStatus('saved-server');
    } finally {
      setSaving(false);
    }
  };

  const generateDescriptions = async () => {
    setGeneratingDescs(true);
    try {
      const headers = getAuthHeaders();
      const res = await axios.post(`${API}/admin/generate-contribution-descriptions`, {
        journey_name: form.name,
        poetic_name: form.poetic_name || '',
        description: form.description || ''
      }, { headers, withCredentials: true });
      if (res.data?.descriptions) update('contribution_descriptions', res.data.descriptions);
    } catch (err) {
      alert('Erro ao gerar descricoes com IA');
    } finally {
      setGeneratingDescs(false);
    }
  };

  const generateStoryChapters = async () => {
    setGeneratingStory(true);
    try {
      const headers = getAuthHeaders();
      const res = await axios.post(`${API}/admin/generate-story-chapters`, {
        journey_name: form.name,
        poetic_name: form.poetic_name || '',
        description: form.description || ''
      }, { headers, withCredentials: true });
      if (res.data?.chapters) update('story_chapters', res.data.chapters);
    } catch (err) {
      alert('Erro ao gerar capitulos com IA');
    } finally {
      setGeneratingStory(false);
    }
  };

  const FieldError = ({ field }) => errors[field] ? (
    <p className="text-red-500 text-xs mt-1 flex items-center gap-1" data-testid={`error-${field}`}>
      <AlertCircle className="w-3 h-3" /> {errors[field]}
    </p>
  ) : null;

  const inputClass = (field) =>
    `w-full px-4 py-2.5 bg-white border rounded-xl focus:outline-none focus:ring-2 transition-colors ${
      errors[field] ? 'border-red-300 focus:ring-red-300/50' : 'border-stone-200 focus:ring-[#FFBE98]/50'
    }`;

  const PreviewPanel = () => (
    <div className="bg-stone-900 rounded-xl overflow-hidden" data-testid="journey-preview">
      <div className="relative h-40">
        {form.image_url ? (
          <img src={form.image_url} alt="Preview" className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full bg-stone-700 flex items-center justify-center text-stone-500">Sem imagem</div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
        <div className="absolute bottom-3 left-4">
          <p className="text-white font-bold text-lg">{form.name || 'Nome do destino'}</p>
          <p className="text-[#FFBE98] text-sm italic">{form.poetic_name || ''}</p>
        </div>
      </div>
      <div className="p-4 space-y-2">
        {form.goal_amount > 0 && (
          <div>
            <div className="flex justify-between text-xs text-stone-400 mb-1">
              <span>Progresso</span>
              <span>{form.goal_amount > 0 ? Math.round((form.current_amount || 0) / form.goal_amount * 100) : 0}%</span>
            </div>
            <div className="h-1.5 bg-stone-700 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-[#FFBE98] to-[#F2C94C] rounded-full"
                style={{ width: `${Math.min((form.current_amount || 0) / form.goal_amount * 100, 100)}%` }} />
            </div>
          </div>
        )}
        {form.emotional_message && <p className="text-stone-300 text-xs italic">"{form.emotional_message}"</p>}
        {(() => {
          const ch = form.story_chapters?.[String(form.current_chapter || 1)];
          return ch?.title ? (
            <div className="bg-stone-800 rounded-lg p-2">
              <p className="text-[#FFBE98] text-xs font-bold">Cap. {form.current_chapter || 1}: {ch.title}</p>
              {ch.lines?.[0] && <p className="text-stone-400 text-xs mt-1">{ch.lines[0]}</p>}
            </div>
          ) : null;
        })()}
      </div>
    </div>
  );

  return (
    <div className="bg-white rounded-2xl border border-stone-200 shadow-lg overflow-hidden" data-testid="journey-edit-form">
      {/* Restore Banner */}
      <AnimatePresence>
        {showRestoreBanner && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
            className="bg-blue-50 border-b border-blue-200 px-6 py-3 flex items-center justify-between" data-testid="autosave-restore-banner">
            <div className="flex items-center gap-2 text-sm text-blue-700">
              <Cloud className="w-4 h-4" />
              <span>
                {draftSource === 'server' 
                  ? 'Rascunho recuperado do servidor. Deseja mante-lo?' 
                  : 'Dados recuperados de uma sessao anterior. Deseja mante-los?'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => setShowRestoreBanner(false)}
                className="px-3 py-1 text-xs font-semibold text-blue-700 bg-blue-100 rounded-lg hover:bg-blue-200 transition-colors"
                data-testid="autosave-keep-btn">
                Manter
              </button>
              <button onClick={discardRestore}
                className="px-3 py-1 text-xs font-semibold text-stone-600 bg-stone-100 rounded-lg hover:bg-stone-200 transition-colors"
                data-testid="autosave-discard-btn">
                Descartar
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-stone-200 bg-stone-50">
        <div className="flex items-center gap-3">
          <h3 className="font-bold text-lg text-[#2D2A26]">Editar: {form.name}</h3>
          <AnimatePresence>
            {hasChanges && (
              <motion.span initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
                className="px-2.5 py-0.5 bg-amber-100 text-amber-700 rounded-full text-xs font-semibold" data-testid="unsaved-indicator">
                Alteracoes por guardar
              </motion.span>
            )}
          </AnimatePresence>
          <AnimatePresence>
            {autosaveStatus && (
              <motion.span initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}
                className={`flex items-center gap-1 text-xs ${autosaveStatus === 'saved-local' ? 'text-amber-600' : 'text-green-600'}`} data-testid="autosave-indicator">
                <Cloud className="w-3 h-3" /> 
                {autosaveStatus === 'saved-local' ? 'Guardado localmente' : 'Sincronizado'}
              </motion.span>
            )}
          </AnimatePresence>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowPreview(!showPreview)}
            className={`p-2 rounded-lg transition-colors ${showPreview ? 'bg-[#FFBE98]/20 text-[#FFBE98]' : 'hover:bg-stone-200 text-[#6B6661]'}`}
            data-testid="toggle-preview-btn" title="Preview">
            <Eye className="w-5 h-5" />
          </button>
          <button onClick={onCancel} className="p-2 hover:bg-stone-200 rounded-lg transition-colors">
            <X className="w-5 h-5 text-[#6B6661]" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-stone-200 px-6 bg-stone-50/50">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors -mb-px ${
              tab === t.id
                ? 'border-[#FFBE98] text-[#2D2A26]'
                : 'border-transparent text-[#6B6661] hover:text-[#2D2A26] hover:border-stone-300'
            }`} data-testid={`tab-${t.id}`}>
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Body */}
      <div className="flex">
        <div className={`p-6 ${showPreview ? 'flex-1' : 'w-full'}`} data-testid="form-content">
          <div style={{ display: tab === 'basico' ? 'block' : 'none' }}>
            <div className="space-y-6">
              <div>
                <h4 className="font-semibold text-[#2D2A26] flex items-center gap-2 mb-4">
                  <MapPin className="w-4 h-4 text-[#FFBE98]" /> Informacoes Basicas
                </h4>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[#6B6661] mb-1">Nome do Destino *</label>
                    <input type="text" value={form.name || ''} onChange={e => update('name', e.target.value)}
                      placeholder="Ex: China, Japao, Brasil..." className={inputClass('name')} data-testid="edit-name" />
                    <FieldError field="name" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#6B6661] mb-1">Titulo Poetico</label>
                    <input type="text" value={form.poetic_name || ''} onChange={e => update('poetic_name', e.target.value)}
                      placeholder="Ex: Onde os Dragoes Dancam" className={inputClass('poetic_name')} data-testid="edit-poetic-name" />
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-[#2D2A26] flex items-center gap-2 mb-4">
                  <Target className="w-4 h-4 text-[#FFBE98]" /> Objetivos Financeiros
                </h4>
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[#6B6661] mb-1">Objetivo (€) *</label>
                    <input type="number" value={form.goal_amount || ''} onChange={e => update('goal_amount', parseFloat(e.target.value) || 0)}
                      min="100" className={inputClass('goal_amount')} data-testid="edit-goal" />
                    <FieldError field="goal_amount" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#6B6661] mb-1">Ja Angariado (€)</label>
                    <input type="number" value={form.current_amount || 0} disabled
                      className="w-full px-4 py-2.5 bg-stone-100 border border-stone-200 rounded-xl text-[#6B6661]" />
                    <p className="text-xs text-[#6B6661] mt-1">Calculado automaticamente</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#6B6661] mb-1">Data Objetivo</label>
                    <input type="date" value={form.target_date || ''} onChange={e => update('target_date', e.target.value)}
                      className={inputClass('target_date')} data-testid="edit-target-date" />
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-[#2D2A26] flex items-center gap-2 mb-4">
                  <Image className="w-4 h-4 text-[#FFBE98]" /> Imagem
                </h4>
                <div className="flex gap-4 items-start">
                  <div className="w-32 h-24 rounded-xl overflow-hidden border border-stone-200 bg-stone-100 flex-shrink-0">
                    {form.image_url ? (
                      <img src={form.image_url} alt="Preview" className="w-full h-full object-cover"
                        onError={e => { e.target.style.display = 'none'; }} />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-stone-400">
                        <Image className="w-8 h-8" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-[#6B6661] mb-1">URL da Imagem</label>
                    <input type="url" value={form.image_url || ''} onChange={e => update('image_url', e.target.value)}
                      placeholder="https://..." className={inputClass('image_url')} data-testid="edit-image-url" />
                    <FieldError field="image_url" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div style={{ display: tab === 'conteudo' ? 'block' : 'none' }}>
            <div className="space-y-6">
              <div>
                <h4 className="font-semibold text-[#2D2A26] flex items-center gap-2 mb-4">
                  <FileText className="w-4 h-4 text-[#FFBE98]" /> Textos e Descricoes
                </h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-[#6B6661] mb-1">Mensagem Emocional</label>
                    <textarea value={form.emotional_message || ''} onChange={e => update('emotional_message', e.target.value)}
                      placeholder="Mensagem que aparece em destaque na pagina da viagem..." rows={2}
                      className={`${inputClass('emotional_message')} resize-none`} data-testid="edit-emotional" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#6B6661] mb-1">Descricao do Impacto</label>
                    <textarea value={form.impact_description || ''} onChange={e => update('impact_description', e.target.value)}
                      placeholder="Descreva o impacto que esta viagem tera..." rows={2}
                      className={`${inputClass('impact_description')} resize-none`} data-testid="edit-impact" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#6B6661] mb-1">Descricao Completa</label>
                    <textarea value={form.description || ''} onChange={e => update('description', e.target.value)}
                      placeholder="Descricao detalhada da viagem..." rows={3}
                      className={`${inputClass('description')} resize-none`} data-testid="edit-description" />
                  </div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-[#2D2A26] flex items-center gap-2">
                    <Heart className="w-4 h-4 text-[#FFBE98]" /> Descricoes de Contribuicao
                    <span className="text-xs font-normal text-[#6B6661]">(aparece no checkout)</span>
                  </h4>
                  <button type="button" onClick={generateDescriptions}
                    disabled={generatingDescs || !form.name}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-[#FFBE98] to-[#F2C94C] text-[#2D2A26] rounded-lg text-xs font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
                    data-testid="generate-ai-descriptions-btn">
                    {generatingDescs ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                    {generatingDescs ? 'A gerar...' : 'Gerar com IA'}
                  </button>
                </div>
                <div className="grid md:grid-cols-2 gap-3">
                  {[10, 20, 50, 100, 200, 500, 1000].map(amt => (
                    <div key={amt} className="flex items-center gap-2">
                      <span className="text-sm font-bold text-[#2D2A26] min-w-[50px]">€{amt}</span>
                      <input type="text"
                        value={(form.contribution_descriptions || {})[String(amt)] || ''}
                        onChange={e => {
                          const descs = { ...(form.contribution_descriptions || {}) };
                          if (e.target.value) descs[String(amt)] = e.target.value;
                          else delete descs[String(amt)];
                          update('contribution_descriptions', descs);
                        }}
                        placeholder="Ex: Uma experiencia especial..."
                        className="flex-1 px-3 py-2 bg-white border border-stone-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#FFBE98]/50"
                        data-testid={`contrib-desc-${amt}`} />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div style={{ display: tab === 'storytelling' ? 'block' : 'none' }}>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-[#2D2A26] flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-[#FFBE98]" /> Capitulos da Historia
                </h4>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-[#6B6661]">
                    Capitulo atual: <strong className="text-[#FFBE98]">{form.current_chapter || 1}</strong>
                  </span>
                  <label className="flex items-center gap-1.5 text-xs cursor-pointer">
                    <input type="checkbox"
                      checked={form.story_emails_enabled !== false}
                      onChange={e => update('story_emails_enabled', e.target.checked)}
                      className="rounded border-stone-300 text-[#FFBE98] focus:ring-[#FFBE98]/50" />
                    <span className="text-[#6B6661]">Emails automaticos</span>
                  </label>
                </div>
              </div>

              <button type="button" onClick={generateStoryChapters}
                disabled={generatingStory || !form.name}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-[#FFBE98]/10 to-[#F2C94C]/10 border border-[#FFBE98]/30 text-[#2D2A26] rounded-xl text-sm font-semibold hover:from-[#FFBE98]/20 hover:to-[#F2C94C]/20 transition-all disabled:opacity-50"
                data-testid="generate-ai-story-btn">
                {generatingStory ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4 text-[#FFBE98]" />}
                {generatingStory ? 'A gerar 5 capitulos com IA...' : 'Gerar Storytelling com IA'}
              </button>

              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map(ch => {
                  const chapters = form.story_chapters || {};
                  const chapter = chapters[String(ch)] || {};
                  const isCurrent = (form.current_chapter || 1) === ch;
                  const ranges = ['0% – 25%', '25% – 50%', '50% – 75%', '75% – 100%', '100%+'];
                  return (
                    <div key={ch} className={`border rounded-xl p-4 transition-colors ${isCurrent ? 'border-[#FFBE98] bg-[#FFBE98]/5' : 'border-stone-200 hover:border-stone-300'}`}>
                      <div className="flex items-center gap-2 mb-3">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${isCurrent ? 'bg-[#FFBE98]/20 text-[#FFBE98]' : 'bg-stone-100 text-[#6B6661]'}`}>
                          Cap. {ch}
                        </span>
                        <span className="text-xs text-[#6B6661]">{ranges[ch - 1]}</span>
                        {isCurrent && <span className="text-xs text-[#FFBE98] font-semibold ml-auto">Ativo</span>}
                      </div>
                      <input type="text" value={chapter.title || ''}
                        onChange={e => {
                          const chs = JSON.parse(JSON.stringify(form.story_chapters || {}));
                          if (!chs[String(ch)]) chs[String(ch)] = {};
                          chs[String(ch)].title = e.target.value;
                          update('story_chapters', chs);
                        }}
                        placeholder="Titulo do capitulo" data-testid={`story-chapter-title-${ch}`}
                        className="w-full px-3 py-2 bg-white border border-stone-200 rounded-lg text-sm font-semibold mb-2 focus:outline-none focus:ring-2 focus:ring-[#FFBE98]/50" />
                      <textarea value={(chapter.lines || []).join('\n')}
                        onChange={e => {
                          const chs = JSON.parse(JSON.stringify(form.story_chapters || {}));
                          if (!chs[String(ch)]) chs[String(ch)] = {};
                          chs[String(ch)].lines = e.target.value.split('\n');
                          update('story_chapters', chs);
                        }}
                        placeholder="Texto do capitulo (uma linha por paragrafo)" rows={3}
                        data-testid={`story-chapter-text-${ch}`}
                        className="w-full px-3 py-2 bg-white border border-stone-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#FFBE98]/50 resize-none" />
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div style={{ display: tab === 'config' ? 'block' : 'none' }}>
            <div className="space-y-6">
              <div>
                <h4 className="font-semibold text-[#2D2A26] flex items-center gap-2 mb-4">
                  <Mail className="w-4 h-4 text-[#FFBE98]" /> Emails
                </h4>
                <div className="bg-stone-50 rounded-xl p-4">
                  <div className="flex flex-wrap gap-2">
                    {journey.status !== 'financiada' && form.goal_amount > 0 && (form.current_amount || 0) / form.goal_amount * 100 >= 100 && (
                      <button onClick={() => onEmailPreview && onEmailPreview({
                        previewUrl: `/admin/emails/preview/dream-funded/${journey.journey_id}`,
                        sendUrl: `/admin/emails/dream-funded/${journey.journey_id}`,
                        title: `Preview: Sonho Financiado — ${journey.name}`
                      })} className="px-3 py-2 bg-purple-100 text-purple-700 rounded-lg text-xs font-semibold hover:bg-purple-200 transition-colors flex items-center gap-1.5"
                        data-testid={`send-funded-email-${journey.journey_id}`}>
                        <Heart className="w-3.5 h-3.5" /> Anunciar Sonho Financiado
                      </button>
                    )}
                    {!journey.announcement_email_sent && (
                      <button onClick={() => onEmailPreview && onEmailPreview({
                        previewUrl: `/admin/emails/preview/new-journey/${journey.journey_id}`,
                        sendUrl: `/admin/emails/new-journey/${journey.journey_id}`,
                        title: `Preview: Anunciar — ${journey.name}`
                      })} className="px-3 py-2 bg-blue-100 text-blue-700 rounded-lg text-xs font-semibold hover:bg-blue-200 transition-colors flex items-center gap-1.5"
                        data-testid={`send-new-journey-email-${journey.journey_id}`}>
                        <Mail className="w-3.5 h-3.5" /> Anunciar Novo Sonho
                      </button>
                    )}
                    {journey.announcement_email_sent && (
                      <span className="px-3 py-2 bg-stone-100 text-stone-500 rounded-lg text-xs flex items-center gap-1.5">
                        <CheckCircle className="w-3.5 h-3.5" /> Anuncio enviado
                      </span>
                    )}
                    {journey.funded_email_sent && (
                      <span className="px-3 py-2 bg-stone-100 text-stone-500 rounded-lg text-xs flex items-center gap-1.5">
                        <CheckCircle className="w-3.5 h-3.5" /> Email financiado enviado
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-[#2D2A26] flex items-center gap-2 mb-4">
                  <Settings className="w-4 h-4 text-[#FFBE98]" /> Estado e Visibilidade
                </h4>
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[#6B6661] mb-1">Estado</label>
                    <select value={form.is_active} onChange={e => update('is_active', e.target.value === 'true')}
                      className="w-full px-4 py-2.5 bg-white border border-stone-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#FFBE98]/50">
                      <option value="true">Ativa (visivel)</option>
                      <option value="false">Inativa (oculta)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#6B6661] mb-1">Viagem Principal</label>
                    <select value={form.is_main_trip || false} onChange={e => update('is_main_trip', e.target.value === 'true')}
                      className="w-full px-4 py-2.5 bg-white border border-stone-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#FFBE98]/50">
                      <option value="true">Sim (destaque na homepage)</option>
                      <option value="false">Nao</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-3 pt-6">
                    <input type="checkbox" id="show-goal"
                      checked={form.show_goal_amount || false}
                      onChange={e => update('show_goal_amount', e.target.checked)}
                      className="w-5 h-5 rounded border-stone-300 text-[#FFBE98] focus:ring-[#FFBE98]" />
                    <label htmlFor="show-goal" className="text-sm text-[#6B6661] cursor-pointer">
                      Mostrar valor € objetivo
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Preview Sidebar */}
        <AnimatePresence>
          {showPreview && (
            <motion.div initial={{ width: 0, opacity: 0 }} animate={{ width: 280, opacity: 1 }} exit={{ width: 0, opacity: 0 }}
              className="border-l border-stone-200 p-4 bg-stone-50 overflow-hidden flex-shrink-0">
              <p className="text-xs font-semibold text-[#6B6661] uppercase tracking-wider mb-3">Preview</p>
              <PreviewPanel />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-6 py-4 border-t border-stone-200 bg-stone-50">
        <button onClick={() => { clearAutosave(); onCancel(); }} className="px-6 py-2.5 text-[#6B6661] hover:bg-stone-200 rounded-xl transition-colors" data-testid="edit-cancel-btn">
          Cancelar
        </button>
        <button onClick={handleSave} disabled={saving || !hasChanges}
          className="px-6 py-2.5 bg-[#2D2A26] text-white rounded-xl hover:bg-[#4A4640] transition-colors flex items-center gap-2 disabled:opacity-50"
          data-testid="edit-save-btn">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          {saving ? 'A guardar...' : 'Guardar Alteracoes'}
        </button>
      </div>
    </div>
  );
};

export default JourneyEditForm;
