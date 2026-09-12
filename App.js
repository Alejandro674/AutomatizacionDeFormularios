import React, { useState } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  StyleSheet, 
  ScrollView, 
  Switch, 
  Alert,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator
} from 'react-native';

export default function AppAutomator() {
  const [formUrl, setFormUrl] = useState('');
  const [cantidad, setCantidad] = useState('5');
  const [requiereGoogle, setRequiereGoogle] = useState(false);
  
  // --- ESTADO DE CARGA PARA BLOQUEAR UI ---
  const [isLoading, setIsLoading] = useState(false);
  
  // --- ESTADOS PARA TEXTOS CORTOS AGRUPADOS POR PREGUNTA ---
  const [preguntaCorto, setPreguntaCorto] = useState('');
  const [respuestaCortoTemporal, setRespuestaCortoTemporal] = useState('');
  const [respuestasCortasTemp, setRespuestasCortasTemp] = useState([]);
  const [listaCortosAgrupados, setListaCortosAgrupados] = useState([]);

  // --- ESTADOS PARA PÁRRAFOS LARGOS AGRUPADOS POR PREGUNTA ---
  const [preguntaLargo, setPreguntaLargo] = useState('');
  const [respuestaLargoTemporal, setRespuestaLargoTemporal] = useState('');
  const [respuestasLargasTemp, setRespuestasLargasTemp] = useState([]);
  const [listaLargosAgrupados, setListaLargosAgrupados] = useState([]);

  // Funciones para Textos Cortos
  const agregarOpcionCortoTemp = () => {
    if (respuestaCortoTemporal.trim() !== '') {
      setRespuestasCortasTemp([...respuestasCortasTemp, respuestaCortoTemporal.trim()]);
      setRespuestaCortoTemporal('');
    }
  };

  const guardarGrupoCorto = () => {
    if (preguntaCorto.trim() !== '' && respuestasCortasTemp.length > 0) {
      setListaCortosAgrupados([
        ...listaCortosAgrupados,
        { pregunta: preguntaCorto.trim(), respuestas: respuestasCortasTemp }
      ]);
      setPreguntaCorto('');
      setRespuestasCortasTemp([]);
    } else {
      Alert.alert("Aviso", "Escribe una pregunta y al menos una respuesta corta.");
    }
  };

  const eliminarGrupoCorto = (index) => {
    setListaCortosAgrupados(listaCortosAgrupados.filter((_, i) => i !== index));
  };

  // Funciones para Párrafos Largos
  const agregarOpcionLargoTemp = () => {
    if (respuestaLargoTemporal.trim() !== '') {
      setRespuestasLargasTemp([...respuestasLargasTemp, respuestaLargoTemporal.trim()]);
      setRespuestaLargoTemporal('');
    }
  };

  const guardarGrupoLargo = () => {
    if (preguntaLargo.trim() !== '' && respuestasLargasTemp.length > 0) {
      setListaLargosAgrupados([
        ...listaLargosAgrupados,
        { pregunta: preguntaLargo.trim(), respuestas: respuestasLargasTemp }
      ]);
      setPreguntaLargo('');
      setRespuestasLargasTemp([]);
    } else {
      Alert.alert("Aviso", "Escribe una pregunta de párrafo y al menos un texto largo.");
    }
  };

  const eliminarGrupoLargo = (index) => {
    setListaLargosAgrupados(listaLargosAgrupados.filter((_, i) => i !== index));
  };

  // Conexión con tu Backend en Python (FastAPI)
  const enviarAlBackend = async () => {
    if (!formUrl.trim()) {
      Alert.alert("Error", "Por favor ingresa la URL del formulario.");
      return;
    }

    setIsLoading(true); // Bloquea la UI e inicia la barra de carga

    const payload = {
      url: formUrl,
      iteraciones: parseInt(cantidad) || 1,
      requiereLoginGoogle: requiereGoogle,
      textosCortosConfig: listaCortosAgrupados,
      textosLargosConfig: listaLargosAgrupados
    };

    console.log("Enviando payload al servidor:", payload);

    try {
      // ⚠️ REEMPLAZA '192.168.X.X' CON LA IP REAL DE TU COMPUTADORA
      const response = await fetch('http://192.168.100.14:8000/ejecutar-bot', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const resultado = await response.json();
      console.log("Respuesta del servidor:", resultado);
      Alert.alert("Éxito", resultado.message || "¡Automatización finalizada en el servidor!");
    } catch (error) {
      console.error("Error al conectar con el backend:", error);
      Alert.alert("Error de Conexión", "No se pudo comunicar con el servidor Python. Revisa la IP y que Uvicorn esté corriendo.");
    } finally {
      setIsLoading(false); // Libera el botón al terminar
    }
  };

  return (
    <KeyboardAvoidingView 
      style={{ flex: 1, backgroundColor: '#F5F7FA' }} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView 
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title}>🤖 Automatizador de Forms</Text>

        <Text style={styles.label}>URL del Formulario</Text>
        <TextInput
          style={styles.input}
          placeholder="https://docs.google.com/forms/..."
          value={formUrl}
          onChangeText={setFormUrl}
          autoCapitalize="none"
          editable={!isLoading}
        />

        <View style={styles.row}>
          <Text style={styles.label}>Cantidad de formularios</Text>
          <TextInput
            style={[styles.input, styles.shortInput]}
            placeholder="Ej: 5"
            value={cantidad}
            onChangeText={setCantidad}
            keyboardType="numeric"
            maxLength={4}
            editable={!isLoading}
          />
        </View>

        <View style={styles.switchContainer}>
          <View style={styles.switchTextGroup}>
            <Text style={styles.switchTitle}>Verificación de Google</Text>
            <Text style={styles.switchSubtitle}>
              {requiereGoogle ? 'Usará credenciales de sesión' : 'Envío anónimo'}
            </Text>
          </View>
          <Switch
            trackColor={{ false: '#d3d3d3', true: '#a1c4fd' }}
            thumbColor={requiereGoogle ? '#007BFF' : '#f4f3f4'}
            onValueChange={setRequiereGoogle}
            value={requiereGoogle}
            disabled={isLoading}
          />
        </View>

        {/* --- SECCIÓN 1: TEXTOS CORTOS POR PREGUNTA --- */}
        <View style={styles.cardSection}>
          <Text style={styles.sectionHeader}>Configurar Texto Corto</Text>
          <TextInput
            style={styles.input}
            placeholder="Nombre de la pregunta (Ej: Nombre)"
            value={preguntaCorto}
            onChangeText={setPreguntaCorto}
            editable={!isLoading}
          />

          <View style={[styles.inputRow, { marginTop: 8 }]}>
            <TextInput
              style={[styles.input, styles.flexInput]}
              placeholder="Añadir una respuesta posible..."
              value={respuestaCortoTemporal}
              onChangeText={setRespuestaCortoTemporal}
              editable={!isLoading}
            />
            <TouchableOpacity 
              style={[styles.addButtonSecundary, isLoading && { opacity: 0.5 }]} 
              onPress={agregarOpcionCortoTemp}
              disabled={isLoading}
            >
              <Text style={styles.addButtonText}>+ Respuesta</Text>
            </TouchableOpacity>
          </View>

          {respuestasCortasTemp.map((res, i) => (
            <Text key={i} style={styles.tempSubText}>• {res}</Text>
          ))}

          <TouchableOpacity 
            style={[styles.saveGroupButton, isLoading && { opacity: 0.5 }]} 
            onPress={guardarGrupoCorto}
            disabled={isLoading}
          >
            <Text style={styles.buttonText}>Guardar Pregunta Corta</Text>
          </TouchableOpacity>
        </View>

        {listaCortosAgrupados.map((item, index) => (
          <View key={index} style={styles.savedCard}>
            <View style={{ flex: 1 }}>
              <Text style={styles.savedTitle}>Pregunta: {item.pregunta}</Text>
              <Text style={styles.savedDesc}>Respuestas: {item.respuestas.join(', ')}</Text>
            </View>
            <TouchableOpacity onPress={() => eliminarGrupoCorto(index)} disabled={isLoading}>
              <Text style={styles.deleteText}>X</Text>
            </TouchableOpacity>
          </View>
        ))}

        {/* --- SECCIÓN 2: PÁRRAFOS LARGOS POR PREGUNTA --- */}
        <View style={styles.cardSection}>
          <Text style={styles.sectionHeader}>Configurar Párrafo Largo</Text>
          <TextInput
            style={styles.input}
            placeholder="Nombre de la pregunta (Ej: Conclusiones)"
            value={preguntaLargo}
            onChangeText={setPreguntaLargo}
            editable={!isLoading}
          />

          <View style={[styles.inputRow, { marginTop: 8 }]}>
            <TextInput
              style={[styles.input, styles.flexInput, styles.textAreaSmall]}
              placeholder="Añadir un párrafo posible..."
              value={respuestaLargoTemporal}
              onChangeText={setRespuestaLargoTemporal}
              multiline={true}
              editable={!isLoading}
            />
            <TouchableOpacity 
              style={[styles.addButtonSecundary, { height: 40 }, isLoading && { opacity: 0.5 }]} 
              onPress={agregarOpcionLargoTemp}
              disabled={isLoading}
            >
              <Text style={styles.addButtonText}>+ Párrafo</Text>
            </TouchableOpacity>
          </View>

          {respuestasLargasTemp.map((res, i) => (
            <Text key={i} style={styles.tempSubText}>💬 {res}</Text>
          ))}

          <TouchableOpacity 
            style={[styles.saveGroupButton, isLoading && { opacity: 0.5 }]} 
            onPress={guardarGrupoLargo}
            disabled={isLoading}
          >
            <Text style={styles.buttonText}>Guardar Pregunta de Párrafo</Text>
          </TouchableOpacity>
        </View>

        {listaLargosAgrupados.map((item, index) => (
          <View key={index} style={styles.savedCard}>
            <View style={{ flex: 1 }}>
              <Text style={styles.savedTitle}>Pregunta: {item.pregunta}</Text>
              <Text style={styles.savedDesc}>Párrafos: {item.respuestas.join(' | ')}</Text>
            </View>
            <TouchableOpacity onPress={() => eliminarGrupoLargo(index)} disabled={isLoading}>
              <Text style={styles.deleteText}>X</Text>
            </TouchableOpacity>
          </View>
        ))}

        {/* --- BOTÓN CONDICIONAL O BARRA DE CARGA --- */}
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#007BFF" />
            <Text style={styles.loadingText}>
              {parseInt(cantidad) > 1 
                ? `Procesando ${cantidad} formularios. No cierres la app...` 
                : 'Enviando formulario, por favor espera...'}
            </Text>
          </View>
        ) : (
          <TouchableOpacity style={styles.mainButton} onPress={enviarAlBackend}>
            <Text style={styles.mainButtonText}>Iniciar Automatización</Text>
          </TouchableOpacity>
        )}
        
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, backgroundColor: '#F5F7FA', flexGrow: 1 },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 15, color: '#333', textAlign: 'center' },
  label: { fontSize: 14, fontWeight: '600', color: '#555', marginTop: 10, marginBottom: 5 },
  sectionHeader: { fontSize: 15, fontWeight: 'bold', color: '#007BFF', marginBottom: 8 },
  input: { backgroundColor: '#FFF', borderWidth: 1, borderColor: '#DDD', borderRadius: 8, padding: 10, fontSize: 15, color: '#333' },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 10 },
  shortInput: { width: 80, textAlign: 'center' },
  switchContainer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#FFF', padding: 12, borderRadius: 8, borderWidth: 1, borderColor: '#DDD', marginTop: 15 },
  switchTextGroup: { flex: 1, paddingRight: 10 },
  switchTitle: { fontSize: 15, fontWeight: '600', color: '#333' },
  switchSubtitle: { fontSize: 11, color: '#888', marginTop: 2 },
  cardSection: { backgroundColor: '#FFF', padding: 15, borderRadius: 10, borderWidth: 1, borderColor: '#CBD5E1', marginTop: 20 },
  inputRow: { flexDirection: 'row', alignItems: 'center' },
  flexInput: { flex: 1, marginRight: 8 },
  textAreaSmall: { minHeight: 40 },
  addButtonSecundary: { backgroundColor: '#64748B', paddingVertical: 10, paddingHorizontal: 12, borderRadius: 8, justifyContent: 'center' },
  addButtonText: { color: '#FFF', fontWeight: 'bold', fontSize: 12 },
  tempSubText: { fontSize: 12, color: '#666', marginTop: 4, marginLeft: 5 },
  saveGroupButton: { backgroundColor: '#10B981', padding: 10, borderRadius: 8, marginTop: 12, alignItems: 'center' },
  savedCard: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#FFF', padding: 12, borderRadius: 8, borderWidth: 1, borderColor: '#93C5FD', marginTop: 8 },
  savedTitle: { fontSize: 13, fontWeight: 'bold', color: '#1E293B' },
  savedDesc: { fontSize: 12, color: '#475569', marginTop: 2 },
  deleteText: { color: '#EF4444', fontWeight: 'bold', fontSize: 16, paddingHorizontal: 8 },
  mainButton: { backgroundColor: '#007BFF', padding: 15, borderRadius: 8, marginTop: 25, marginBottom: 20, alignItems: 'center' },
  mainButtonText: { color: '#FFF', fontSize: 16, fontWeight: 'bold' },
  loadingContainer: { marginTop: 25, marginBottom: 20, alignItems: 'center', padding: 15, backgroundColor: '#E0F2FE', borderRadius: 8, borderWidth: 1, borderColor: '#BAE6FD' },
  loadingText: { marginTop: 10, fontSize: 14, color: '#0369A1', fontWeight: 'bold', textAlign: 'center' }
});