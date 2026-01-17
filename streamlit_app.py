import React, { useState, useEffect, useMemo } from 'react';
import { initializeApp } from 'firebase/app';
import { 
  getAuth, 
  signInAnonymously, 
  signInWithCustomToken,
  onAuthStateChanged 
} from 'firebase/auth';
import { 
  getFirestore, 
  collection, 
  addDoc, 
  onSnapshot, 
  serverTimestamp,
  query
} from 'firebase/firestore';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell
} from 'recharts';

// Firebase configuration
const firebaseConfig = JSON.parse(__firebase_config);
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const appId = typeof __app_id !== 'undefined' ? __app_id : 'hipnotrading-audit-v1';

const App = () => {
  const [user, setUser] = useState(null);
  const [allAudits, setAllAudits] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [accessCode, setAccessCode] = useState("");
  
  // Filtros de Fecha para Análisis
  const [filterStartDate, setFilterStartDate] = useState("");
  const [filterEndDate, setFilterEndDate] = useState("");
  
  // Estado para el Modal de Evaluación
  const [showModal, setShowModal] = useState(false);
  const [modalContent, setModalContent] = useState(null);

  const today = new Date().toISOString().split('T')[0];

  const initialFormState = {
    nombreTrader: '', 
    fechaAuditoria: today,
    horaInicioSesion: '09:00',
    energiaMetabolica: 7,
    ritualCoherencia: 'No',
    revisadoPlan: 'No', 
    estadoSistemaNervioso: '🟢 Vagal Ventral (Calma Activa)',
    indiceCoherenciaIC: 90,
    sesgosNeuroCognitivos: [],
    marcadoresSomaticos: [],
    nivelPresencia: 9,
    respetoStopTP: 10,
    dejoCorrerPlan: 10,
    numEntradasTotales: 0,
    pnlDia: 0,
    numEntradasPlan: 0,
    numEntradasFueraPlan: 0,
    resultadoConsecuenciaPlan: '', 
    numPerdidasHoy: 0,
    aceptoRiesgo: '', // Nuevo campo solicitado para sección 3.1
    emocionesPorPerdida: {}, 
    tiposPorPerdida: {},
    sensacionCorporalPerdida: '',
    estadoSistemaNerviosoFinal: '',
    sensacionCorporal: '',
    detallesSesion: '',
    emocionesDetectadas: [], 
    objetivoReal: 'Aprender/Proceso',
    nivelCoherencia: 5,
    pnlEmocional: 'He ganado disciplina',
    anclajeIdentidad: 7,
    creenciasInstaladas: [],
    reescrituraNarrativa: '',
    visualizacionesCierre: [],
    aprendizajeMentor: '',
    protocoloReactivacionVagal: '',
    compromisoManana: ''
  };

  const [formData, setFormData] = useState(initialFormState);

  useEffect(() => {
    const initAuth = async () => {
      try {
        if (typeof __initial_auth_token !== 'undefined' && __initial_auth_token) {
          await signInWithCustomToken(auth, __initial_auth_token);
        } else {
          await signInAnonymously(auth);
        }
      } catch (error) {
        console.error("Error de autenticación:", error);
      }
    };
    initAuth();
    const unsubscribe = onAuthStateChanged(auth, setUser);
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (!user) return;
    const auditsRef = collection(db, 'artifacts', appId, 'public', 'data', 'weekly_audits');
    const q = query(auditsRef);
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const data = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      const sorted = data.sort((a, b) => (a.createdAt?.seconds || 0) - (b.createdAt?.seconds || 0));
      setAllAudits(sorted);
    }, (error) => console.error("Error en Firestore:", error));
    return () => unsubscribe();
  }, [user, appId]);

  const uniqueTradersList = useMemo(() => {
    const names = allAudits.map(a => a.nombreTrader?.trim()).filter(Boolean);
    return Array.from(new Set(names)).sort();
  }, [allAudits]);

  // Lógica de filtrado centralizada: Nombre + Rango de Fechas
  const filteredAudits = useMemo(() => {
    let filtered = allAudits;

    // 1. Filtro por nombre
    const search = formData.nombreTrader.trim().toLowerCase();
    if (search) {
      filtered = filtered.filter(a => a.nombreTrader?.trim().toLowerCase() === search);
    } else {
      return []; // Si no hay nombre, no mostramos nada
    }

    // 2. Filtro por fecha inicio
    if (filterStartDate) {
      filtered = filtered.filter(a => {
        const date = a.fechaAuditoria || a.fechaLocal; // Preferimos fechaAuditoria (YYYY-MM-DD)
        return date >= filterStartDate;
      });
    }

    // 3. Filtro por fecha fin
    if (filterEndDate) {
      filtered = filtered.filter(a => {
        const date = a.fechaAuditoria || a.fechaLocal;
        return date <= filterEndDate;
      });
    }

    return filtered;
  }, [allAudits, formData.nombreTrader, filterStartDate, filterEndDate]);

  const chartData = useMemo(() => {
    return filteredAudits.map(audit => ({
      fecha: audit.fechaAuditoria || audit.fechaLocal,
      ic: parseFloat(audit.indiceCoherenciaIC) || 0,
      presencia: parseFloat(audit.nivelPresencia) || 0,
      energia: parseFloat(audit.energiaMetabolica) || 0
    }));
  }, [filteredAudits]);

  const disciplineFactor = useMemo(() => {
    const total = parseInt(formData.numPerdidasHoy) || 0;
    if (total === 0) return { percent: 100, color: 'bg-emerald-500', label: '100%', textColor: 'text-emerald-500' };

    let cleanCount = 0;
    let definedCount = 0;

    for (let i = 1; i <= total; i++) {
      const type = formData.tiposPorPerdida[i];
      if (type) {
        definedCount++;
        if (type === 'Limpia ✨ (Bajo Plan)') {
          cleanCount++;
        }
      }
    }

    if (definedCount === 0) return { percent: 0, color: 'bg-slate-400', label: '0%', textColor: 'text-slate-400' };
    const percentage = Math.round((cleanCount / total) * 100);
    let color = 'bg-amber-500'; 
    let textColor = 'text-amber-500';
    if (percentage >= 80) { color = 'bg-emerald-500'; textColor = 'text-emerald-500'; }
    if (percentage < 50) { color = 'bg-rose-600'; textColor = 'text-rose-600'; }

    return { percent: percentage, color, label: `${percentage}%`, textColor };
  }, [formData.numPerdidasHoy, formData.tiposPorPerdida]);

  const correlationChartData = useMemo(() => {
    return [
      { name: 'IC Inicial', value: parseInt(formData.indiceCoherenciaIC) || 0, color: '#6366f1' },
      { name: 'Disciplina Final', value: disciplineFactor.percent, color: disciplineFactor.percent < 50 ? '#e11d48' : '#10b981' }
    ];
  }, [formData.indiceCoherenciaIC, disciplineFactor]);

  const heatmapData = useMemo(() => {
    const grid = {};
    const hours = [8, 9, 10, 11, 12, 13, 14, 15, 16];
    const days = [1, 2, 3, 4, 5]; 

    days.forEach(d => {
      hours.forEach(h => {
        grid[`${d}-${h}`] = { 
          totalIC: 0, 
          totalPnL: 0, 
          count: 0,
          avgIC: 0,
          avgPnL: 0
        };
      });
    });

    filteredAudits.forEach(audit => {
      let dateObj;
      
      if (audit.timestampSesion && audit.timestampSesion.seconds) {
          dateObj = new Date(audit.timestampSesion.seconds * 1000);
      } else if (audit.createdAt && typeof audit.createdAt.seconds === 'number') {
          dateObj = new Date(audit.createdAt.seconds * 1000);
      } else if (audit.fechaAuditoria) {
          const parts = audit.fechaAuditoria.split('-');
          const hourParts = (audit.horaInicioSesion || "10:00").split(':');
          if (parts.length === 3) {
              dateObj = new Date(parts[0], parts[1] - 1, parts[2], parseInt(hourParts[0]), parseInt(hourParts[1]));
          }
      }
      
      if (!dateObj || isNaN(dateObj.getTime())) return;

      const day = dateObj.getDay(); 
      const hour = dateObj.getHours();

      if (day >= 1 && day <= 5 && hour >= 8 && hour <= 16) {
        const key = `${day}-${hour}`;
        if (grid[key]) {
          grid[key].totalIC += parseFloat(audit.indiceCoherenciaIC || 0);
          grid[key].totalPnL += parseFloat(audit.pnlDia || 0);
          grid[key].count += 1;
        }
      }
    });

    Object.keys(grid).forEach(key => {
      if (grid[key].count > 0) {
        grid[key].avgIC = Math.round(grid[key].totalIC / grid[key].count);
        grid[key].avgPnL = parseFloat((grid[key].totalPnL / grid[key].count).toFixed(2));
      }
    });

    return grid;
  }, [filteredAudits]);

  const getHeatmapColor = (cell) => {
    if (cell.count === 0) return 'bg-[#E0E0E0]'; 
    const { avgIC, avgPnL } = cell;
    if (avgIC < 50 || avgPnL < 0) return 'bg-[#F44336]'; 
    if (avgIC >= 50 && avgIC < 65) return 'bg-[#FFC107]'; 
    if (avgIC >= 65 && avgPnL >= 0) return 'bg-[#4CAF50]'; 
    return 'bg-[#4CAF50]'; 
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    if (type === 'checkbox') {
      const list = formData[name] || [];
      setFormData(prev => ({
        ...prev,
        [name]: checked ? [...list, value] : list.filter(i => i !== value)
      }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleEmocionPerdida = (index, emocion) => {
    setFormData(prev => ({
      ...prev,
      emocionesPorPerdida: { ...prev.emocionesPorPerdida, [index]: emocion }
    }));
  };

  const handleTipoPerdida = (index, tipo) => {
    setFormData(prev => ({
      ...prev,
      tiposPorPerdida: { ...prev.tiposPorPerdida, [index]: tipo }
    }));
  };

  const evaluatePreMarket = () => {
    const ic = parseInt(formData.indiceCoherenciaIC);
    const sn = formData.estadoSistemaNervioso;
    const presencia = parseInt(formData.nivelPresencia);
    const plan = formData.revisadoPlan;
    
    let content = { title: '', text: '', colorClass: '', buttonClass: '' };

    if (ic < 60 || sn.includes('Dorsal') || presencia < 4 || plan === 'No') {
      content = {
        title: '🛑 SISTEMA NO APTO',
        text: plan === 'No' 
          ? 'Falta de disciplina operativa: NO has revisado tu plan de trading. Sin mapa, no hay trading. Revisa el plan y vuelve a validar.'
          : 'Tu coherencia o presencia es crítica. En este estado, tu córtex prefrontal está desactivado y operarás bajo el miedo, la disociación o la parálisis. PROHIBIDO OPERAR. Realiza una sesión de hipnosis de emergencia.',
        colorClass: 'bg-rose-600',
        buttonClass: 'bg-rose-700 hover:bg-rose-800'
      };
    } else if (ic >= 70 && sn.includes('Vagal Ventral') && presencia >= 9 && plan === 'Sí') {
      content = {
        title: '✅ SISTEMA OPTIMIZADO',
        text: 'Estás en estado de flujo, tu coherencia es alta y tu foco es total. Tu biología está preparada para ejecutar el plan sin interferencias emocionales. ¡Buen trading!',
        colorClass: 'bg-emerald-500',
        buttonClass: 'bg-emerald-700 hover:bg-emerald-800'
      };
    } else {
      content = {
        title: '⚠️ PRECAUCIÓN',
        text: 'Tu sistema muestra signos de alerta, urgencia o falta de foco. Estás en la frontera del secuestro emocional. Opera con lotaje reducido o realiza 2 minutos de coherencia cardíaca antes del primer trade.',
        colorClass: 'bg-amber-500',
        buttonClass: 'bg-amber-600 hover:bg-amber-700'
      };
    }

    setModalContent(content);
    setShowModal(true);
  };

  const saveAudit = async (e) => {
    e.preventDefault();
    if (!formData.nombreTrader.trim()) {
      setMessage({ type: 'error', text: 'El nombre del trader es obligatorio.' });
      return;
    }
    setLoading(true);
    try {
      const auditsRef = collection(db, 'artifacts', appId, 'public', 'data', 'weekly_audits');
      const fechaFormateada = new Date(formData.fechaAuditoria).toLocaleDateString();
      
      const [año, mes, dia] = formData.fechaAuditoria.split('-');
      const [horas, minutos] = formData.horaInicioSesion.split(':');
      const timestampCompleto = new Date(año, mes - 1, dia, horas, minutos);

      await addDoc(auditsRef, {
        ...formData,
        nombreTrader: formData.nombreTrader.trim(),
        createdAt: serverTimestamp(),
        timestampSesion: timestampCompleto,
        fechaLocal: fechaFormateada
      });

      setMessage({ type: 'success', text: 'Registro neurobiológico guardado correctamente.' });
      setFormData({ ...initialFormState, nombreTrader: formData.nombreTrader });
      setTimeout(() => setMessage(null), 4000);
    } catch (error) {
      setMessage({ type: 'error', text: 'Error al guardar datos.' });
    } finally {
      setLoading(false);
    }
  };

  const SectionTitle = ({ number, title }) => (
    <div className="bg-slate-900 p-5 text-white flex items-center gap-4 border-b border-indigo-500/30">
      <span className="bg-indigo-600 text-[11px] w-7 h-7 flex items-center justify-center rounded-full font-black shadow-lg shadow-indigo-500/20">{number}</span>
      <h2 className="text-sm font-black uppercase tracking-[0.15em]">{title}</h2>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#f8fafc] p-4 md:p-8 text-slate-800 font-sans selection:bg-indigo-100">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12 text-center">
          <h1 className="text-5xl font-black text-slate-900 tracking-tighter uppercase mb-3 text-transparent bg-clip-text bg-gradient-to-r from-slate-900 to-indigo-700 italic">Auditoría Neuro-Biología Trading</h1>
          <div className="h-1.5 w-24 bg-indigo-600 mx-auto rounded-full mb-4"></div>
          <p className="text-slate-500 font-bold italic text-sm">HIPNOTRADING - Supervisión de Coherencia y Sistema Nervioso</p>
        </header>

        <form onSubmit={saveAudit} className="space-y-10">
          <section className="bg-white rounded-[2rem] shadow-xl shadow-slate-200/50 border border-slate-200 p-8 border-l-[16px] border-l-indigo-600">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2 space-y-6">
                {accessCode === "COACH2024" && uniqueTradersList.length > 0 && (
                  <div className="bg-amber-50 p-4 rounded-2xl border border-amber-200 mb-4 animate-in slide-in-from-top-2">
                    <label className="block text-[10px] font-black text-amber-700 uppercase tracking-widest mb-2 italic">Panel de Coach: Seleccionar Trader</label>
                    <select 
                      onChange={(e) => setFormData(prev => ({...prev, nombreTrader: e.target.value}))}
                      className="w-full p-3 bg-white border-2 border-amber-200 rounded-xl text-sm font-black text-amber-900 outline-none"
                    >
                      <option value="">-- Ver lista de traders --</option>
                      {uniqueTradersList.map(name => (
                        <option key={name} value={name}>{name}</option>
                      ))}
                    </select>
                  </div>
                )}
                
                <div>
                  <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3 italic">Nombre del Trader</label>
                  <input type="text" name="nombreTrader" value={formData.nombreTrader} onChange={handleInputChange} placeholder="Introduce tu nombre..." className="w-full p-4 bg-slate-50 border-2 border-slate-100 rounded-2xl text-xl font-black text-indigo-700 outline-none focus:border-indigo-500 transition-all" required />
                </div>

                {/* NUEVO PANEL DE FILTROS DE FECHA */}
                <div className="bg-indigo-50/50 p-4 rounded-2xl border border-indigo-100">
                  <label className="block text-[10px] font-black text-indigo-800 uppercase tracking-widest mb-2 italic flex items-center gap-2">
                    <span>📅 Filtrar Análisis por Periodo</span>
                    <span className="text-indigo-400 font-normal normal-case">(Opcional: Dejar vacío para ver todo el histórico)</span>
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-[9px] font-bold text-slate-500 uppercase block mb-1">Desde:</span>
                      <input 
                        type="date" 
                        value={filterStartDate} 
                        onChange={(e) => setFilterStartDate(e.target.value)} 
                        className="w-full p-2 bg-white border border-indigo-200 rounded-xl text-xs font-bold text-slate-700 outline-none" 
                      />
                    </div>
                    <div>
                      <span className="text-[9px] font-bold text-slate-500 uppercase block mb-1">Hasta:</span>
                      <input 
                        type="date" 
                        value={filterEndDate} 
                        onChange={(e) => setFilterEndDate(e.target.value)} 
                        className="w-full p-2 bg-white border border-indigo-200 rounded-xl text-xs font-bold text-slate-700 outline-none" 
                      />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-black text-indigo-600 uppercase tracking-widest mb-3 italic">Fecha Registro</label>
                    <input type="date" name="fechaAuditoria" value={formData.fechaAuditoria} onChange={handleInputChange} className="w-full p-4 bg-indigo-50/50 border-2 border-indigo-100 rounded-2xl font-bold text-slate-700 outline-none cursor-pointer" required />
                  </div>
                  <div>
                    <label className="block text-[10px] font-black text-indigo-600 uppercase tracking-widest mb-3 italic">Hora de Inicio de Sesión</label>
                    <input type="time" name="horaInicioSesion" value={formData.horaInicioSesion} onChange={handleInputChange} className="w-full p-4 bg-indigo-50/50 border-2 border-indigo-100 rounded-2xl font-bold text-slate-700 outline-none cursor-pointer" required />
                  </div>
                </div>
              </div>
              <div className="bg-indigo-900 p-6 rounded-3xl text-white flex flex-col justify-center">
                <label className="block text-[10px] font-black text-indigo-300 uppercase tracking-widest mb-3">Acceso Supervisión</label>
                <input type="password" value={accessCode} onChange={(e) => setAccessCode(e.target.value)} placeholder="Código" className="w-full p-4 bg-indigo-800/50 border-2 border-indigo-700 rounded-2xl text-center font-bold outline-none" />
                {accessCode === "COACH2024" && <p className="text-[9px] text-emerald-400 mt-2 text-center font-black uppercase">Modo Coach Activado</p>}
              </div>
            </div>
          </section>

          {/* FASE 1: PRE-MERCADO */}
          <section className="bg-white rounded-[2rem] shadow-sm border border-slate-200 overflow-hidden relative">
            <SectionTitle number="1" title="Fase Pre-Mercado (Check Neurobiológico)" />
            <div className="p-8 space-y-12 pb-12">
              <div className="space-y-4">
                <label className="block text-sm font-black text-slate-700 uppercase tracking-tight">1.1 Nivel de Energía Metabólica (1-10)</label>
                <div className="bg-slate-50 p-6 rounded-3xl border border-slate-100">
                  <div className="flex items-center gap-6 mb-4">
                    <input type="range" min="1" max="10" name="energiaMetabolica" value={formData.energiaMetabolica} onChange={handleInputChange} className="flex-1 h-2 bg-slate-200 rounded-lg accent-indigo-600 cursor-pointer" />
                    <span className="text-4xl font-black text-indigo-600">{formData.energiaMetabolica}</span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-4 text-[10px] font-black uppercase tracking-tighter italic">
                    <div className="bg-rose-50 text-rose-700 p-2 rounded-xl border border-rose-100">1–3 = Energía muy baja (agotado, niebla mental)</div>
                    <div className="bg-amber-50 text-amber-700 p-2 rounded-xl border border-amber-100">4–6 = Energía media (cansado pero funcional)</div>
                    <div className="bg-emerald-50 text-emerald-700 p-2 rounded-xl border border-emerald-100">7–8 = Buena energía (descansado, mente clara)</div>
                    <div className="bg-indigo-50 text-indigo-700 p-2 rounded-xl border border-indigo-100">9–10 = Energía muy alta (mucha activación, vigila la euforia)</div>
                  </div>
                </div>
              </div>

              <div className="space-y-4 max-w-md">
                <label className="block text-sm font-black text-slate-700 uppercase">1.2 Ritual de Coherencia Realizado</label>
                <div className="flex gap-3">
                  {['Sí', 'No'].map(opt => (
                    <button key={opt} type="button" onClick={() => setFormData(prev => ({ ...prev, ritualCoherencia: opt }))} className={`flex-1 py-4 rounded-2xl font-black uppercase text-sm transition-all border-2 ${formData.ritualCoherencia === opt ? 'bg-slate-900 border-slate-900 text-white shadow-lg' : 'bg-white border-slate-100 text-slate-400 hover:border-slate-300'}`}>
                      {opt}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-12 pt-8 border-t border-slate-100">
                <div className="space-y-4">
                  <label className="block text-sm font-black text-slate-700 uppercase">1.3 Estado del Sistema Nervioso (SN)</label>
                  <div className="space-y-3">
                    {[
                      { val: '🟢 Vagal Ventral (Calma Activa)', desc: 'Estado de flujo y claridad' },
                      { val: '🟡 Simpático (Lucha/Caza)', desc: 'Tensión y urgencia (Lobo)' },
                      { val: '🔴 Dorsal Vagal (Parálisis)', desc: 'Miedo y dudas (Perro)' }
                    ].map(st => (
                      <label key={st.val} className={`p-4 border-2 rounded-2xl cursor-pointer transition-all flex justify-between items-center ${formData.estadoSistemaNervioso === st.val ? 'border-indigo-600 bg-indigo-50/50' : 'border-slate-50 bg-slate-50/30'}`}>
                        <div className="flex flex-col"><span className="text-[10px] font-black uppercase">{st.val}</span><span className="text-[9px] font-bold text-slate-400 italic">{st.desc}</span></div>
                        <input type="radio" name="estadoSistemaNervioso" value={st.val} checked={formData.estadoSistemaNervioso === st.val} onChange={handleInputChange} className="accent-indigo-600" />
                      </label>
                    ))}
                  </div>
                </div>

                <div className="space-y-6">
                  <label className="block text-sm font-black text-slate-700 uppercase mb-2">1.4 IC % (Índice de Coherencia)</label>
                  <div className="bg-slate-50 p-6 rounded-3xl border border-slate-100">
                    <div className="flex items-center gap-6 mb-3">
                      <input type="range" min="0" max="100" name="indiceCoherenciaIC" value={formData.indiceCoherenciaIC} onChange={handleInputChange} className="flex-1 h-2 bg-slate-200 rounded-lg accent-emerald-500 cursor-pointer" />
                      <span className="text-3xl font-black text-emerald-600">{formData.indiceCoherenciaIC}%</span>
                    </div>
                  </div>
                  
                  <div className="overflow-hidden rounded-2xl border border-slate-100 shadow-sm">
                    <table className="w-full text-left text-[10px] font-bold uppercase tracking-tighter">
                      <thead className="bg-slate-100 text-slate-500">
                        <tr>
                          <th className="px-3 py-2">IC %</th>
                          <th className="px-3 py-2">Estado</th>
                          <th className="px-3 py-2">Sensación Física</th>
                          <th className="px-3 py-2">Action</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white text-slate-700">
                        <tr className="border-b border-slate-50">
                          <td className="px-3 py-2 text-emerald-600">90-100%</td>
                          <td className="px-3 py-2">Óptimo</td>
                          <td className="px-3 py-2 font-medium">Visión clara, calma</td>
                          <td className="px-3 py-2 font-black text-emerald-600">OPERAR</td>
                        </tr>
                        <tr className="border-b border-slate-50">
                          <td className="px-3 py-2 text-emerald-500">70-80%</td>
                          <td className="px-3 py-2">Estable</td>
                          <td className="px-3 py-2 font-medium">Pulso tranquilo</td>
                          <td className="px-3 py-2 font-black text-emerald-600">OPERAR</td>
                        </tr>
                        <tr className="border-b border-slate-50">
                          <td className="px-3 py-2 text-amber-500">50-60%</td>
                          <td className="px-3 py-2">Alerta</td>
                          <td className="px-3 py-2 font-medium">Ganas de entrar</td>
                          <td className="px-3 py-2 font-black text-amber-500">PAUSA</td>
                        </tr>
                        <tr>
                          <td className="px-3 py-2 text-rose-600">&lt; 40%</td>
                          <td className="px-3 py-2">Caos</td>
                          <td className="px-3 py-2 font-medium">Miedo/Ira</td>
                          <td className="px-3 py-2 font-black text-rose-600">BLOQUEO</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <div className="bg-rose-50 border-2 border-rose-100 p-4 rounded-2xl">
                    <p className="text-[10px] font-black text-rose-700 leading-tight uppercase">
                      ⚠️ <span className="underline">Regla de Oro:</span><br />
                      Con un IC inferior al 60%, el córtex prefrontal se apaga y toma el control la amígdala. <span className="text-rose-900">NO DISPARES. RESPIRA 3 MINUTOS.</span>
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4 pt-8 border-t border-slate-100">
                <label className="block text-sm font-black text-slate-700 uppercase tracking-tight">1.5 Nivel de Presencia (1-10)</label>
                <div className="bg-indigo-50/30 p-6 rounded-3xl border border-indigo-100">
                  <div className="flex items-center gap-6 mb-4">
                    <input type="range" min="1" max="10" name="nivelPresencia" value={formData.nivelPresencia} onChange={handleInputChange} className="flex-1 h-2 bg-indigo-200 rounded-lg accent-indigo-600 cursor-pointer" />
                    <span className="text-4xl font-black text-indigo-700">{formData.nivelPresencia}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-4 text-[10px] font-black uppercase tracking-tighter italic">
                    <div className="bg-indigo-100 text-indigo-800 p-2 rounded-xl border border-indigo-200">9-10: Foco total en el ahora (Cuerpo + Gráfico).</div>
                    <div className="bg-emerald-50 text-emerald-800 p-2 rounded-xl border border-emerald-100">7-8: Foco en el plan, distracciones leves.</div>
                    <div className="bg-amber-50 text-amber-800 p-2 rounded-xl border border-amber-100">5-6: Piloto automático / Mirando el móvil.</div>
                    <div className="bg-rose-50 text-rose-800 p-2 rounded-xl border border-rose-100">&lt; 4: Disociación. Apaga la pantalla.</div>
                  </div>
                </div>
              </div>

              <div className="space-y-4 pt-8 border-t border-slate-100 max-w-md">
                <label className="block text-sm font-black text-slate-700 uppercase">1.6 Revisión del Plan de Trading</label>
                <div className="flex gap-3">
                  {['Sí', 'No'].map(opt => (
                    <button key={opt} type="button" onClick={() => setFormData(prev => ({ ...prev, revisadoPlan: opt }))} className={`flex-1 py-4 rounded-2xl font-black uppercase text-sm transition-all border-2 ${formData.revisadoPlan === opt ? (opt === 'Sí' ? 'bg-emerald-600 border-emerald-600 text-white shadow-lg' : 'bg-rose-600 border-rose-600 text-white shadow-lg') : 'bg-white border-slate-100 text-slate-400 hover:border-slate-300'}`}>
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className="pt-8 text-center">
                 <button type="button" onClick={evaluatePreMarket} className="px-8 py-4 bg-slate-900 hover:bg-indigo-700 text-white rounded-2xl font-black uppercase tracking-widest text-xs shadow-lg transition-all">
                    🔍 Validar Preparación Neurobiológica
                 </button>
              </div>
            </div>
          </section>

          {/* FASE 2: EJECUCIÓN */}
          <section className="bg-white rounded-[2rem] shadow-sm border border-slate-200 overflow-hidden">
            <SectionTitle number="2" title="Ejecución y Foco Atencional" />
            <div className="p-8 space-y-12">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6">
                {[
                  { label: 'Entradas Totales', name: 'numEntradasTotales' },
                  { label: 'Resultado PnL', name: 'pnlDia' },
                  { label: 'Dentro del Plan', name: 'numEntradasPlan' },
                  { label: 'Fuera de Plan', name: 'numEntradasFueraPlan' }
                ].map(f => (
                  <div key={f.name} className="bg-slate-50 p-5 rounded-3xl border border-slate-100">
                    <label className="block text-[9px] font-black text-slate-500 uppercase mb-2 tracking-widest">{f.label}</label>
                    <input type="number" name={f.name} value={formData[f.name]} onChange={handleInputChange} className="w-full bg-transparent text-xl font-black outline-none" />
                  </div>
                ))}
              </div>

              {/* NUEVO PUNTO 2.0 - AÑADIDO SOLICITADO */}
              <div className="space-y-4 pt-6 border-t border-slate-100">
                <div className="flex flex-col gap-2">
                   <label className="block text-sm font-black text-slate-700 uppercase italic">2.0 ¿Es el resultado consecuencia directa de seguir el plan?</label>
                   <p className="text-[10px] font-bold text-slate-500 italic max-w-2xl bg-indigo-50 p-3 rounded-xl border border-indigo-100">
                     Recuerda: Una operación ganadora fuera de plan es una <span className="text-rose-600 font-black">pésima operación</span> porque refuerza hábitos destructivos. El dashboard debe premiar la ejecución, no el dinero.
                   </p>
                </div>
                <div className="flex gap-3 max-w-md">
                  {['Sí', 'No'].map(opt => (
                    <button 
                      key={opt} 
                      type="button" 
                      onClick={() => setFormData(prev => ({ ...prev, resultadoConsecuenciaPlan: opt }))} 
                      className={`flex-1 py-4 rounded-2xl font-black uppercase text-sm transition-all border-2 ${
                        formData.resultadoConsecuenciaPlan === opt 
                          ? (opt === 'Sí' ? 'bg-indigo-600 border-indigo-600 text-white shadow-lg' : 'bg-rose-600 border-rose-600 text-white shadow-lg') 
                          : 'bg-white border-slate-100 text-slate-400 hover:border-slate-300'
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4 pt-6 border-t border-slate-100">
                <label className="block text-sm font-black text-slate-700 uppercase italic">2.1 Marcadores Somáticos Detectados</label>
                <div className="flex flex-wrap gap-3">
                  {['TAQUICARDIA', 'TENSIÓN MANDIBULAR', 'CALOR FACIAL', 'PRESIÓN PECHO', 'INQUIETUD PIERNAS', 'SUDORACIÓN', 'RESPIRACIÓN CORTA'].map(m => (
                    <label key={m} className={`px-5 py-3 rounded-2xl border-2 transition-all cursor-pointer font-black text-[10px] uppercase tracking-tight ${formData.marcadoresSomaticos.includes(m) ? 'bg-rose-600 border-rose-600 text-white shadow-md' : 'bg-white border-slate-100 text-slate-400 hover:border-rose-200'}`}>
                      <input type="checkbox" name="marcadoresSomaticos" value={m} checked={formData.marcadoresSomaticos.includes(m)} onChange={handleInputChange} className="hidden" />
                      {m}
                    </label>
                  ))}
                </div>
              </div>

              <div className="space-y-4 pt-6 border-t border-slate-100">
                <label className="block text-sm font-black text-slate-700 uppercase italic">2.2 Sesgos Detectados Durante la Operativa</label>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[
                    { val: 'RECENCIA', desc: 'Influencia del trade anterior.' },
                    { val: 'IMPACIENCIA', desc: 'Entrar antes de tiempo.' },
                    { val: 'OVERTRADING', desc: 'Operar de más.' },
                    { val: 'REVANCHA', desc: 'Recuperar una pérdida.' },
                    { val: 'CONFIRMACIÓN', desc: 'Ver solo lo que quieres ver.' },
                    { val: 'AVERSIÓN', desc: 'Cerrar rápido por miedo.' }
                  ].map(s => (
                    <label key={s.val} className={`flex flex-col p-4 rounded-2xl border-2 transition-all cursor-pointer ${formData.sesgosNeuroCognitivos.includes(s.val) ? 'bg-indigo-600 border-indigo-600 text-white shadow-md' : 'bg-white border-slate-100 text-slate-400 hover:border-indigo-200'}`}>
                      <input type="checkbox" name="sesgosNeuroCognitivos" value={s.val} checked={formData.sesgosNeuroCognitivos.includes(s.val)} onChange={handleInputChange} className="hidden" />
                      <span className="text-[10px] font-black uppercase mb-1">{s.val}</span>
                      <span className={`text-[9px] font-bold italic ${formData.sesgosNeuroCognitivos.includes(s.val) ? 'text-indigo-100' : 'text-slate-400'}`}>{s.desc}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* FASE 3: ANÁLISIS INTEGRAL DE PÉRDIDAS */}
          <section className="bg-white rounded-[2rem] shadow-sm border border-slate-200 overflow-hidden">
            <SectionTitle number="3" title="Análisis Integral de Pérdidas" />
            <div className="p-8 space-y-10">
              <div className="space-y-6">
                {/* 3.1 COMPLETO: PÉRDIDAS Y RIESGO */}
                <div className="flex flex-col md:flex-row gap-8 items-start">
                  <div className="max-w-md">
                    <label className="block text-sm font-black text-slate-700 uppercase italic mb-2">3.1 ¿Cuántas operaciones perdedoras has tenido hoy?</label>
                    <div className="bg-slate-50 p-5 rounded-3xl border border-slate-100 inline-block min-w-[150px]">
                      <input type="number" name="numPerdidasHoy" value={formData.numPerdidasHoy} onChange={handleInputChange} min="0" className="w-full bg-transparent text-3xl font-black text-rose-600 outline-none" />
                    </div>
                  </div>

                  {/* NUEVA PREGUNTA AÑADIDA SOLICITADA */}
                  <div className="max-w-md flex-1">
                     <label className="block text-sm font-black text-slate-700 uppercase italic mb-2">¿Aceptaste el riesgo antes de entrar?</label>
                     <p className="text-[10px] font-bold text-slate-400 italic mb-2">Si la respuesta es NO, es una operación de JUEGO (Gambling), no de Trading.</p>
                     <div className="flex gap-3">
                      {['Sí', 'No'].map(opt => (
                        <button 
                          key={opt} 
                          type="button" 
                          onClick={() => setFormData(prev => ({ ...prev, aceptoRiesgo: opt }))} 
                          className={`flex-1 py-4 rounded-2xl font-black uppercase text-sm transition-all border-2 ${
                            formData.aceptoRiesgo === opt 
                              ? (opt === 'Sí' ? 'bg-indigo-600 border-indigo-600 text-white shadow-lg' : 'bg-rose-600 border-rose-600 text-white shadow-lg') 
                              : 'bg-white border-slate-100 text-slate-400 hover:border-slate-300'
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex flex-col items-center justify-center py-8 bg-slate-900 rounded-[2.5rem] border-4 border-slate-800 shadow-2xl animate-in zoom-in-95">
                  <span className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em] mb-2 italic">Performance Subconsciente</span>
                  <div className="flex items-center gap-4">
                    <div className="h-1 w-12 bg-indigo-500 rounded-full"></div>
                    <div className="text-7xl font-black text-white tabular-nums tracking-tighter">
                      {disciplineFactor.label}
                    </div>
                    <div className="h-1 w-12 bg-indigo-500 rounded-full"></div>
                  </div>
                  <span className={`mt-3 px-6 py-2 rounded-full text-[11px] font-black uppercase border-2 ${disciplineFactor.textColor} border-current`}>
                    FACTOR DISCIPLINA DE SESIÓN
                  </span>
                </div>

                <div className="space-y-4 pt-6 border-t border-slate-100">
                  <div className="flex flex-col gap-1">
                    <label className="block text-sm font-black text-slate-700 uppercase italic tracking-tight">3.2 Sensación Corporal Durante las Pérdidas</label>
                    <p className="text-[11px] font-black text-rose-600 uppercase italic tracking-wide">¿Dónde sentiste la emoción en tu cuerpo?</p>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      'NUDO EN EL ESTÓMAGO', 
                      'OPRESIÓN EN EL PECHO', 
                      'TENSIÓN EN CUELLO/HOMBROS', 
                      'CALOR EN LA CARA', 
                      'VACÍO EN EL ABDOMEN', 
                      'TENSIÓN MANDIBULAR',
                      'FRÍO EN LAS MANOS',
                      'INQUIETUD EN PIERNAS'
                    ].map(sensacion => (
                      <label key={sensacion} className={`p-4 rounded-xl border-2 transition-all cursor-pointer flex items-center justify-center text-center text-[9px] font-black uppercase leading-tight ${formData.sensacionCorporalPerdida === sensacion ? 'bg-rose-600 border-rose-600 text-white shadow-md' : 'bg-slate-50 border-slate-100 text-slate-400 hover:border-rose-200'}`}>
                        <input type="radio" name="sensacionCorporalPerdida" value={sensacion} checked={formData.sensacionCorporalPerdida === sensacion} onChange={handleInputChange} className="hidden" />
                        {sensacion}
                      </label>
                    ))}
                  </div>
                </div>

                {parseInt(formData.numPerdidasHoy) > 0 && (
                  <div className="space-y-6 animate-in fade-in slide-in-from-top-4 pt-6 border-t border-slate-100">
                    <label className="block text-sm font-black text-slate-700 uppercase italic">Desglose de Pérdidas de Sesión</label>
                    <div className="overflow-hidden rounded-3xl border border-slate-200 shadow-sm">
                      <table className="w-full text-left">
                        <thead className="bg-slate-100 text-slate-400 text-[10px] font-black uppercase">
                          <tr>
                            <th className="px-6 py-4 w-16 text-center">#</th>
                            <th className="px-6 py-4">Emoción Predominante</th>
                            <th className="px-6 py-4">Calificación de la Pérdida</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 bg-white">
                          {Array.from({ length: Math.min(parseInt(formData.numPerdidasHoy), 20) }).map((_, i) => {
                            const index = i + 1;
                            return (
                              <tr key={index} className="hover:bg-slate-50 transition-colors">
                                <td className="px-6 py-4 text-center font-black text-slate-300">{index}</td>
                                <td className="px-6 py-4">
                                  <select value={formData.emocionesPorPerdida[index] || ''} onChange={(e) => handleEmocionPerdida(index, e.target.value)} className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-600 outline-none">
                                    <option value="" disabled>Selecciona...</option>
                                    <option value="Ira">Ira 😤</option><option value="Miedo">Miedo 😨</option><option value="Venganza">Venganza ⚔️</option><option value="Tristeza">Tristeza 😢</option>
                                  </select>
                                </td>
                                <td className="px-6 py-4">
                                  <select value={formData.tiposPorPerdida[index] || ''} onChange={(e) => handleTipoPerdida(index, e.target.value)} className="w-full p-3 border rounded-xl text-xs font-black outline-none">
                                    <option value="" disabled>Califica...</option>
                                    <option value="Limpia ✨ (Bajo Plan)">Limpia ✨ (Bajo Plan)</option>
                                    <option value="Sucia 💩 (Fuera de Plan)">Sucia 💩 (Fuera de Plan)</option>
                                  </select>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>

              <div className="space-y-4 pt-8 border-t border-slate-100">
                <div className="flex flex-col gap-1">
                  <label className="block text-sm font-black text-slate-700 uppercase italic">3.3 Emociones Detectadas Durante la Sesión</label>
                  <p className="text-[11px] font-black text-indigo-600 uppercase italic tracking-wide">Identifica qué emociones visitaron tu mente hoy</p>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {[
                    "ANSIEDAD", "EUFORIA", "FOMO", "VENGANZA", "HESITACIÓN (DUDA)", 
                    "CONFIANZA", "FRUSTRACIÓN", "AVARICIA", "ABURRIMIENTO", "ESPERANZA"
                  ].map(emocion => (
                    <label key={emocion} className={`p-3 rounded-xl border-2 transition-all cursor-pointer flex items-center justify-center text-center text-[9px] font-black uppercase ${formData.emocionesDetectadas.includes(emocion) ? 'bg-indigo-600 border-indigo-600 text-white shadow-md' : 'bg-white border-slate-100 text-slate-400 hover:border-indigo-200'}`}>
                      <input type="checkbox" name="emocionesDetectadas" value={emocion} checked={formData.emocionesDetectadas.includes(emocion)} onChange={handleInputChange} className="hidden" />
                      {emocion}
                    </label>
                  ))}
                </div>
              </div>

              <div className="pt-10 border-t border-slate-100">
                <label className="block text-sm font-black text-slate-700 uppercase italic mb-8 text-center">Gráfico de Correlación: Coherencia vs Disciplina</label>
                <div className="h-[250px] w-full max-w-2xl mx-auto">
                   <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={correlationChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontWeight: 'black', fontSize: 10, fill: '#64748b' }} />
                        <YAxis hide domain={[0, 100]} />
                        <Tooltip cursor={{ fill: '#f8fafc' }} contentStyle={{ borderRadius: '15px', border: 'none', fontWeight: 'bold' }} />
                        <Bar dataKey="value" radius={[10, 10, 0, 0]} barSize={80}>
                          {correlationChartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                   </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-slate-50 p-8 rounded-[2rem] border border-slate-200 text-center">
                <p className="text-slate-700 font-bold text-lg leading-relaxed">
                  Tu coherencia de entrada del <span className="text-indigo-600 font-black">{formData.indiceCoherenciaIC}%</span> resultó en una disciplina del <span className={`${disciplineFactor.textColor} font-black`}>{disciplineFactor.percent}%</span>.
                </p>
                {disciplineFactor.percent < 70 && (
                  <div className="mt-4 p-4 bg-rose-100 border-2 border-rose-200 rounded-2xl flex items-center justify-center gap-3 animate-pulse">
                    <span className="text-2xl">🚨</span>
                    <p className="text-xs font-black text-rose-700 uppercase tracking-tight">
                      AVISO DE SECUESTRO EMOCIONAL: Tu biología ha anulado tu capacidad de ejecución. El córtex prefrontal ha cedido el mando al sistema límbico.
                    </p>
                  </div>
                )}
              </div>

              <div className="space-y-4 pt-6 border-t border-slate-100 bg-indigo-50/30 p-6 rounded-3xl border border-indigo-100">
                 <label className="block text-sm font-black text-indigo-800 uppercase italic tracking-tight">3.4 Estado del Sistema Nervioso Final</label>
                 <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {['🟢 Vagal (Calma/Regulación)', '🟡 Simpático (Activado/Ansioso)', '🔴 Dorsal (Agotado/Colapsado)'].map(estado => (
                       <label key={estado} className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex items-center gap-3 ${formData.estadoSistemaNerviosoFinal === estado ? 'bg-white border-indigo-600 shadow-md text-indigo-700' : 'bg-white/50 border-transparent hover:bg-white text-slate-500'}`}>
                          <input type="radio" name="estadoSistemaNerviosoFinal" value={estado} checked={formData.estadoSistemaNerviosoFinal === estado} onChange={handleInputChange} className="accent-indigo-600" />
                          <span className="text-xs font-black uppercase">{estado}</span>
                       </label>
                    ))}
                 </div>
              </div>
            </div>
          </section>

          {/* SECCIÓN 4: REPROGRAMACIÓN SUBCONSCIENTE POST-SESIÓN */}
          <section className="bg-white rounded-[2rem] shadow-sm border border-slate-200 overflow-hidden">
            <SectionTitle number="4" title="Reprogramación Subconsciente Post-Sesión" />
            <div className="p-8 space-y-12">
              <div className="space-y-4">
                <div className="flex flex-col gap-1">
                  <label className="block text-sm font-black text-slate-700 uppercase italic">4.1 ANCLAJE DE IDENTIDAD (1-10)</label>
                  <p className="text-[11px] font-black text-indigo-600 uppercase italic tracking-wide">"Hoy operé como el trader que quiero ser"</p>
                </div>
                <div className="bg-slate-50 p-6 rounded-3xl border border-slate-100">
                  <div className="flex items-center gap-6 mb-4">
                    <input type="range" min="1" max="10" name="anclajeIdentidad" value={formData.anclajeIdentidad} onChange={handleInputChange} className="flex-1 h-2 bg-slate-200 rounded-lg accent-indigo-600 cursor-pointer" />
                    <span className="text-4xl font-black text-indigo-600">{formData.anclajeIdentidad}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4 pt-8 border-t border-slate-100">
                <label className="block text-sm font-black text-slate-700 uppercase italic">4.2 INSTALACIÓN DE CREENCIA POTENCIADORA</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {[
                    "Soy paciente y espero mi setup perfecto",
                    "Confío en mi sistema y en mi criterio",
                    "Las pérdidas son información, no fracasos",
                    "Opero desde la calma, no desde la necesidad",
                    "Mi valor como trader no depende de un trade",
                    "Soy disciplinado incluso cuando nadie me ve"
                  ].map(creencia => (
                    <label key={creencia} className={`p-4 rounded-xl border-2 transition-all cursor-pointer flex items-center gap-3 text-[10px] font-black uppercase ${formData.creenciasInstaladas.includes(creencia) ? 'bg-indigo-600 border-indigo-600 text-white' : 'bg-slate-50 border-slate-100 text-slate-500 hover:border-indigo-200'}`}>
                      <input type="checkbox" name="creenciasInstaladas" value={creencia} checked={formData.creenciasInstaladas.includes(creencia)} onChange={handleInputChange} className="hidden" />
                      {creencia}
                    </label>
                  ))}
                </div>
              </div>

              <div className="space-y-4 pt-8 border-t border-slate-100">
                <label className="block text-sm font-black text-slate-700 uppercase italic">4.3 REESCRITURA NARRATIVA</label>
                <textarea name="reescrituraNarrativa" value={formData.reescrituraNarrativa} onChange={handleInputChange} placeholder="Escribe aquí tu aprendizaje del día de hoy..." className="w-full p-6 bg-slate-50 border-2 border-slate-100 rounded-3xl text-sm font-bold text-slate-600 outline-none focus:border-indigo-500 transition-all min-h-[120px]" />
              </div>

              <div className="space-y-4 pt-8 border-t border-slate-100">
                <label className="block text-sm font-black text-slate-700 uppercase italic">4.4 VISUALIZACIÓN DE CIERRE</label>
                <div className="space-y-3">
                  {[
                    "He visualizado mi próxima sesión ejecutando perfectamente mi plan",
                    "He agradecido a mi cuerpo por la información que me dio hoy",
                    "He cerrado emocionalmente la sesión (ni euforia ni culpa)"
                  ].map(v => (
                    <label key={v} className={`p-4 rounded-xl border-2 transition-all cursor-pointer flex items-center gap-3 text-[10px] font-black uppercase ${formData.visualizacionesCierre.includes(v) ? 'bg-emerald-600 border-emerald-600 text-white' : 'bg-slate-50 border-slate-100 text-slate-500 hover:border-emerald-200'}`}>
                      <input type="checkbox" name="visualizacionesCierre" value={v} checked={formData.visualizacionesCierre.includes(v)} onChange={handleInputChange} className="hidden" />
                      <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${formData.visualizacionesCierre.includes(v) ? 'border-white' : 'border-slate-300'}`}>
                        {formData.visualizacionesCierre.includes(v) && '✓'}
                      </div>
                      {v}
                    </label>
                  ))}
                </div>
              </div>

              <div className="space-y-4 pt-8 border-t border-slate-100">
                <label className="block text-sm font-black text-slate-700 uppercase italic">4.5 PROTOCOLO DE REACTIVACIÓN VAGAL</label>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[
                    { val: "🫁 Respiración 4-7-8 (3 minutos)", color: "border-blue-200 bg-blue-50 text-blue-700" },
                    { val: "🎵 Música + movimiento", color: "border-purple-200 bg-purple-50 text-purple-700" },
                    { val: "🚶 Caminata consciente", color: "border-green-200 bg-green-50 text-green-700" },
                    { val: "🧊 Exposición al frío", color: "border-cyan-200 bg-cyan-50 text-cyan-700" },
                    { val: "🧘 Meditación guiada", color: "border-indigo-200 bg-indigo-50 text-indigo-700" },
                    { val: "❌ Ninguna (omití el cierre)", color: "border-slate-200 bg-slate-50 text-slate-500" }
                  ].map(protocolo => (
                    <label key={protocolo.val} className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex items-center gap-3 ${formData.protocoloReactivacionVagal === protocolo.val ? `${protocolo.color} border-current shadow-md` : 'bg-white border-slate-100 text-slate-400 hover:bg-slate-50'}`}>
                      <input type="radio" name="protocoloReactivacionVagal" value={protocolo.val} checked={formData.protocoloReactivacionVagal === protocolo.val} onChange={handleInputChange} className="accent-indigo-600" />
                      <span className="text-[10px] font-black uppercase">{protocolo.val}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="space-y-4 pt-8 border-t border-slate-100">
                <label className="block text-sm font-black text-slate-700 uppercase italic">4.6 COMPROMISO CON EL MAÑANA</label>
                <input type="text" name="compromisoManana" value={formData.compromisoManana} onChange={handleInputChange} placeholder="Escribe tu compromiso..." className="w-full p-6 bg-slate-50 border-2 border-slate-100 rounded-3xl text-sm font-bold text-slate-600 outline-none focus:border-indigo-500 transition-all" />
              </div>

            </div>
          </section>

          <div className="text-center py-10">
            {message && <div className={`mb-8 p-5 rounded-3xl text-xs font-black uppercase ${message.type === 'success' ? 'bg-emerald-500 text-white' : 'bg-rose-500 text-white'}`}>{message.text}</div>}
            <button type="submit" disabled={loading} className="px-24 py-7 bg-slate-900 text-white rounded-[2.5rem] font-black text-xl shadow-2xl transition-all hover:bg-indigo-600 uppercase tracking-widest">
              {loading ? 'PROCESANDO...' : 'REGISTRAR SESIÓN NEURO'}
            </button>
          </div>
        </form>

        <section className="mt-16 bg-white rounded-[3rem] shadow-2xl border border-slate-200 p-10">
          <h2 className="text-2xl font-black text-slate-900 uppercase italic tracking-tighter mb-10">Evolución Neuro-Técnica</h2>
          <div className="h-[400px] w-full">
            {chartData.length < 1 ? (
              <div className="h-full flex items-center justify-center bg-slate-50 rounded-[2rem] border-4 border-dashed border-slate-100">
                <p className="text-slate-300 font-black uppercase">Sin registros en este periodo</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="6 6" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="fecha" stroke="#cbd5e1" fontSize={10} fontWeight="900" />
                  <YAxis stroke="#cbd5e1" fontSize={10} fontWeight="900" />
                  <Tooltip contentStyle={{ borderRadius: '20px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }} />
                  <Line type="monotone" dataKey="ic" stroke="#10b981" strokeWidth={5} dot={{ r: 6 }} />
                  <Line type="monotone" dataKey="presencia" stroke="#6366f1" strokeWidth={3} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </section>

        <section className="mt-16 bg-white rounded-[3rem] shadow-2xl border border-slate-200 overflow-hidden">
          <div className="bg-slate-900 p-8 text-white">
            <h2 className="text-xl font-black uppercase tracking-widest italic">Historial Detallado de Auditorías</h2>
            <p className="text-slate-400 text-[10px] font-bold uppercase mt-1">Registros completos para análisis de progresión subconsciente</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left min-w-[1000px]">
              <thead className="bg-slate-50 text-slate-500 text-[10px] font-black uppercase tracking-tighter">
                <tr>
                  <th className="px-6 py-4 border-b">Fecha</th>
                  <th className="px-6 py-4 border-b">Hora Inicio</th>
                  <th className="px-6 py-4 border-b">IC Inicial</th>
                  <th className="px-6 py-4 border-b">Energía</th>
                  <th className="px-6 py-4 border-b">Presencia</th>
                  <th className="px-6 py-4 border-b">Plan Rev.</th>
                  <th className="px-6 py-4 border-b">PnL Diaro</th>
                  <th className="px-6 py-4 border-b">Eficiencia Plan</th>
                  <th className="px-6 py-4 border-b">Identidad</th>
                  <th className="px-6 py-4 border-b">SN Final</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredAudits.length > 0 ? (
                  filteredAudits.slice().reverse().map((audit) => {
                    const totalE = parseInt(audit.numEntradasTotales) || 0;
                    const planE = parseInt(audit.numEntradasPlan) || 0;
                    const eficiencia = totalE > 0 ? Math.round((planE / totalE) * 100) : 0;
                    
                    return (
                      <tr key={audit.id} className="hover:bg-indigo-50/30 transition-colors">
                        <td className="px-6 py-4 font-black text-slate-900 text-xs">{audit.fechaAuditoria || audit.fechaLocal}</td>
                        <td className="px-6 py-4 font-bold text-indigo-500 text-xs">{audit.horaInicioSesion || "-"}</td>
                        <td className="px-6 py-4">
                          <span className={`px-3 py-1 rounded-full text-[10px] font-black ${parseInt(audit.indiceCoherenciaIC) >= 70 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                            {audit.indiceCoherenciaIC}%
                          </span>
                        </td>
                        <td className="px-6 py-4 font-bold text-slate-600 text-xs">{audit.energiaMetabolica}/10</td>
                        <td className="px-6 py-4 font-bold text-slate-600 text-xs">{audit.nivelPresencia}/10</td>
                        <td className="px-6 py-4 font-black text-xs">
                          {audit.revisadoPlan === 'Sí' ? <span className="text-emerald-600">SÍ</span> : <span className="text-rose-600">NO</span>}
                        </td>
                        <td className={`px-6 py-4 font-black text-xs ${parseFloat(audit.pnlDia) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                          {audit.pnlDia}
                        </td>
                        <td className="px-6 py-4">
                          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden max-w-[80px]">
                            <div className="h-full bg-indigo-500" style={{ width: `${eficiencia}%` }}></div>
                          </div>
                          <span className="text-[9px] font-black text-slate-400 mt-1 block">{eficiencia}%</span>
                        </td>
                        <td className="px-6 py-4 font-bold text-indigo-600 text-xs">{audit.anclajeIdentidad}/10</td>
                        <td className="px-6 py-4 text-[9px] font-black text-slate-500 max-w-[150px] truncate uppercase">{audit.estadoSistemaNerviosoFinal || '-'}</td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan="10" className="px-6 py-12 text-center text-slate-300 font-black uppercase tracking-widest text-xs italic">
                      No hay registros que coincidan con los filtros seleccionados
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="mt-16 bg-white rounded-[3rem] shadow-2xl border border-slate-200 overflow-hidden mb-20">
          <div className="bg-indigo-900 p-8 text-white">
            <h2 className="text-xl font-black uppercase tracking-widest italic">Historial de Reprogramación y Cierre (Punto 4)</h2>
            <p className="text-indigo-300 text-[10px] font-bold uppercase mt-1">Monitoreo de anclajes de identidad y protocolos vagales</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left min-w-[1000px]">
              <thead className="bg-indigo-50/50 text-indigo-900/40 text-[10px] font-black uppercase tracking-tighter">
                <tr>
                  <th className="px-6 py-4 border-b">Fecha</th>
                  <th className="px-6 py-4 border-b">Anclaje Identidad</th>
                  <th className="px-6 py-4 border-b">Protocolo Vagal</th>
                  <th className="px-6 py-4 border-b">Creencias Instaladas</th>
                  <th className="px-6 py-4 border-b">Cierres Realizados</th>
                  <th className="px-6 py-4 border-b">Narrativa / Compromiso</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredAudits.length > 0 ? (
                  filteredAudits.slice().reverse().map((audit) => (
                    <tr key={`p4-${audit.id}`} className="hover:bg-indigo-50/20 transition-colors">
                      <td className="px-6 py-4 font-black text-slate-900 text-xs">{audit.fechaAuditoria || audit.fechaLocal}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className={`w-8 h-8 rounded-lg flex items-center justify-center font-black text-[10px] ${parseInt(audit.anclajeIdentidad) >= 8 ? 'bg-emerald-500 text-white' : 'bg-amber-500 text-white'}`}>
                            {audit.anclajeIdentidad}
                          </span>
                          <span className="text-[9px] font-bold text-slate-400 uppercase tracking-tight italic">/10</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 font-black text-[10px] text-indigo-700 uppercase italic">
                        {audit.protocoloReactivacionVagal || 'No registrado'}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1 max-w-[250px]">
                          {audit.creenciasInstaladas && audit.creenciasInstaladas.length > 0 ? (
                            audit.creenciasInstaladas.map((c, idx) => (
                              <span key={idx} className="bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-md text-[8px] font-black uppercase border border-indigo-100">
                                {c}
                              </span>
                            ))
                          ) : <span className="text-slate-300 italic text-[9px]">Sin creencias</span>}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1">
                          <span className="text-emerald-500 font-black text-xs">
                            {audit.visualizacionesCierre ? audit.visualizacionesCierre.length : 0}
                          </span>
                          <span className="text-[9px] font-bold text-slate-400 uppercase">/3 Pasos</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="max-w-[300px]">
                          <p className="text-[10px] font-bold text-slate-600 italic line-clamp-2 mb-1">
                            "{audit.reescrituraNarrativa || 'Sin narrativa...'}"
                          </p>
                          <p className="text-[9px] font-black text-indigo-600 uppercase tracking-tighter truncate border-t border-slate-50 pt-1">
                            🎯 {audit.compromisoManana || 'Sin compromiso'}
                          </p>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center text-slate-300 font-black uppercase tracking-widest text-xs italic">
                      Sin datos de reprogramación en este periodo
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* MAPA DE CALOR: RENDIMIENTO TEMPORAL */}
        <section className="mt-16 bg-white rounded-[3rem] shadow-2xl border border-slate-200 overflow-hidden mb-20">
          <div className="bg-slate-900 p-8 text-white flex justify-between items-center">
            <div>
              <h2 className="text-xl font-black uppercase tracking-widest italic">📊 Mapa de Calor: Rendimiento Temporal</h2>
              <p className="text-slate-400 text-[10px] font-bold uppercase mt-1">Identifica en qué momentos tu sistema nervioso está más regulado</p>
            </div>
            { (filterStartDate || filterEndDate) && (
               <div className="bg-indigo-600 px-4 py-2 rounded-xl text-[10px] font-black uppercase animate-pulse">
                  Filtro Activo
               </div>
            )}
          </div>
          
          <div className="p-10 overflow-x-auto">
            <div className="min-w-[800px] grid grid-cols-6 gap-2">
              <div className="h-12"></div>
              {['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'].map(d => (
                <div key={d} className="h-12 flex items-center justify-center font-black text-xs uppercase text-slate-500 tracking-wider">
                  {d}
                </div>
              ))}

              {[8, 9, 10, 11, 12, 13, 14, 15, 16].map(hour => (
                <React.Fragment key={hour}>
                  <div className="h-20 flex items-center justify-end pr-4 font-black text-xs text-slate-400">
                    {`${hour.toString().padStart(2, '0')}:00`}
                  </div>
                  {[1, 2, 3, 4, 5].map(day => {
                    const key = `${day}-${hour}`;
                    const cell = heatmapData[key] || { count: 0, avgIC: 0, avgPnL: 0 };
                    const bgColor = getHeatmapColor(cell);
                    return (
                      <div 
                        key={key} 
                        className={`group relative h-20 rounded-xl ${bgColor} transition-all duration-300 hover:scale-105 hover:shadow-lg flex flex-col items-center justify-center cursor-pointer`}
                      >
                         {cell.count > 0 && (
                            <div className="text-white text-center">
                              <div className="text-xs font-black">{cell.avgIC}% IC</div>
                              <div className="text-[10px] font-bold opacity-90">${cell.avgPnL}</div>
                            </div>
                         )}
                         <div className="absolute z-10 bottom-full mb-2 hidden group-hover:block w-48 bg-slate-800 text-white p-3 rounded-xl shadow-xl border border-slate-700">
                            <div className="text-[10px] font-black uppercase text-slate-400 mb-1">
                              {['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'][day]} - {hour}:00
                            </div>
                            <div className="flex justify-between text-xs font-bold mb-1">
                               <span>Promedio IC:</span>
                               <span className={cell.avgIC >= 65 ? 'text-emerald-400' : 'text-rose-400'}>{cell.avgIC}%</span>
                            </div>
                            <div className="flex justify-between text-xs font-bold mb-1">
                               <span>Promedio PnL:</span>
                               <span className={cell.avgPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}>${cell.avgPnL}</span>
                            </div>
                            <div className="flex justify-between text-xs font-bold border-t border-slate-700 pt-1 mt-1">
                               <span>Sesiones registradas:</span>
                               <span>{cell.count}</span>
                            </div>
                         </div>
                      </div>
                    );
                  })}
                </React.Fragment>
              ))}
            </div>

            <div className="mt-8 flex flex-wrap gap-4 justify-center text-[10px] font-black uppercase text-slate-500">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-[#4CAF50]"></div>
                <span>Óptimo: IC ≥65% + PnL ≥ 0</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-[#FFC107]"></div>
                <span>Alerta: IC 50-64%</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-[#F44336]"></div>
                <span>Crítico: IC &lt;50% o PnL negativo</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-[#E0E0E0]"></div>
                <span>Sin datos</span>
              </div>
            </div>
          </div>
        </section>

      </div>

      {showModal && modalContent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm">
          <div className="bg-white rounded-[2rem] max-w-lg w-full shadow-2xl overflow-hidden animate-in zoom-in-95 border border-white/20">
             <div className={`${modalContent.colorClass} p-8 text-white text-center`}><h3 className="text-3xl font-black uppercase italic tracking-tighter">{modalContent.title}</h3></div>
             <div className="p-8 text-center space-y-8 bg-white"><p className="text-slate-600 font-bold text-lg leading-relaxed">{modalContent.text}</p><button onClick={() => setShowModal(false)} className={`w-full py-4 rounded-2xl font-black uppercase tracking-widest text-white shadow-xl text-xs ${modalContent.buttonClass}`}>Entiendo</button></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
