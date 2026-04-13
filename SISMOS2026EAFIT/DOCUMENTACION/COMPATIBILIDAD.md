# Compatibilidad y Requisitos del Sistema

## Soporte de Dispositivos

### Dispositivos Soportados

La aplicación **Visor Cartográfico** está optimizada para funcionar en múltiples dispositivos:

| Dispositivo          | Resolución Mínima | Estado    | Experiencia                                        |
| -------------------- | ------------------- | --------- | -------------------------------------------------- |
| **Escritorio** | 1200px × 768px     | Óptimo   | Experiencia completa con todas las funcionalidades |
| **Laptop**     | 1024px × 768px     | Óptimo   | Experiencia completa                               |
| **Tablet**     | 768px × 1024px     | Funcional | Algunas limitaciones de espacio                    |
| **Móvil**     | 360px × 640px      | Limitado  | Funcionalidad básica, navegación simplificada    |

---

## Recomendación de Uso

### **Experiencia Óptima: Escritorio/Laptop**

Para aprovechar al máximo todas las funcionalidades de la aplicación, se recomienda:

- **Resolución mínima**: 1366 × 768 píxeles
- **Resolución recomendada**: 1920 × 1080 píxeles (Full HD)
- **Navegadores soportados**: Chrome 90+, Firefox 88+, Edge 90+, Safari 14+

### ¿Por qué Escritorio?

La aplicación maneja:

- **Mapas interactivos complejos** con múltiples capas
- **Dashboards con múltiples gráficos** simultáneos
- **Tablas de datos extensas** con muchas columnas
- **Visualizaciones detalladas** que requieren espacio

---

## Adaptaciones Responsive

### Tablet (768px - 1199px)

**Cambios Automáticos:**

- Sidebar colapsable
- Gráficos apilados en 2 columnas
- Tablas con scroll horizontal
- Tarjetas KPI en 2 columnas

**Limitaciones:**

- Algunos gráficos pueden requerir scroll
- Tooltips pueden ser menos precisos

### Móvil (<768px)

**Cambios Automáticos:**

- Menú hamburguesa (sidebar oculto por defecto)
- Gráficos apilados verticalmente (1 columna)
- Tarjetas KPI apiladas
- Tablas con scroll horizontal y sombras indicadoras
- Controles táctiles optimizados (pinch-to-zoom)

**Limitaciones Importantes:**

- **Mapas**: Interacción limitada, tooltips simplificados
- **Tablas**: Requieren scroll horizontal extenso
- **Gráficos**: Pueden ser difíciles de leer en pantallas pequeñas
- **Dashboard**: Experiencia fragmentada por falta de espacio
- **Análisis simultáneo**: No es posible ver múltiples gráficos a la vez

---

## Navegadores Soportados

### Completamente Soportados

- **Google Chrome** 90+ (Recomendado)
- **Microsoft Edge** 90+
- **Mozilla Firefox** 88+
- **Safari** 14+ (macOS/iOS)

### Parcialmente Soportados

- **Opera** 76+
- **Brave** 1.24+

### No Soportados

- Internet Explorer (cualquier versión)
- Navegadores móviles antiguos (<2020)

---

## Requisitos Técnicos

### Hardware Mínimo

**Para Escritorio:**

- **Procesador**: Intel Core i3 / AMD Ryzen 3 o superior
- **RAM**: 4 GB mínimo, 8 GB recomendado
- **Conexión**: 5 Mbps (primera carga), 1 Mbps (uso continuo)

**Para Móvil/Tablet:**

- **Procesador**: Snapdragon 660 / Apple A10 o superior
- **RAM**: 3 GB mínimo
- **Conexión**: 3 Mbps recomendado

### Software

- **JavaScript**: Debe estar habilitado
- **Cookies**: Permitidas para la sesión
- **WebGL**: Recomendado para renderizado de mapas
- **LocalStorage**: Habilitado (para persistencia de estado)

---

## Optimización por Dispositivo

### En Escritorio

**Ventajas:**

- Vista completa del dashboard sin scroll
- Mapas con tooltips detallados
- Múltiples gráficos visibles simultáneamente
- Tablas con todas las columnas visibles
- Navegación rápida entre secciones

**Recomendaciones:**

- Usar pantalla completa (F11) para máxima inmersión
- Zoom del navegador al 100% para mejor legibilidad
- Usar mouse para interacciones precisas en el mapa

### En Tablet

**Ventajas:**

- Portabilidad
- Gestos táctiles (pinch-to-zoom)
- Funcionalidad completa con adaptaciones

**Recomendaciones:**

- Usar en modo horizontal (landscape)
- Cerrar sidebar cuando no se use para maximizar espacio
- Usar zoom del navegador si los textos son pequeños

### En Móvil

**Ventajas:**

- Acceso desde cualquier lugar
- Consultas rápidas de datos
- Visualización básica del mapa

**Limitaciones:**

- No recomendado para análisis profundo
- Experiencia fragmentada
- Requiere mucho scroll

**Recomendaciones:**

- **Usar solo para consultas rápidas**
- Rotar a modo horizontal
- Usar WiFi para mejor rendimiento
- Considerar usar tablet o escritorio para análisis completo

---

## 📊 Comparativa de Funcionalidades

| Funcionalidad          | Escritorio         | Tablet            | Móvil         |
| ---------------------- | ------------------ | ----------------- | -------------- |
| Mapa Interactivo       | Completo           | Completo          | Limitado       |
| Tooltips Detallados    | Sí                | Simplificados     | Básicos       |
| Dashboard Completo     | Visible            | Con scroll        | Fragmentado    |
| Gráficos Simultáneos | 2-3                | 1-2               | 1              |
| Tablas Completas       | Todas las columnas | Scroll horizontal | Scroll extenso |
| Análisis Detallado    | Óptimo            | Funcional         | Difícil       |
| Exportación (futuro)  | Sí                | Sí               | Limitado       |
| Performance            | Excelente          | Bueno             | Aceptable      |

---

## Solución de Problemas

### Problemas Comunes en Móvil

**Problema**: Mapa no responde al touch

- **Solución**: Desactivar scroll de página, usar dos dedos para pan

**Problema**: Tablas ilegibles

- **Solución**: Rotar a horizontal, usar zoom del navegador

**Problema**: Sidebar no se cierra

- **Solución**: Tocar fuera del sidebar o el overlay oscuro

### Problemas Comunes en Tablet

**Problema**: Gráficos muy pequeños

- **Solución**: Cerrar sidebar, usar zoom del navegador

**Problema**: Tooltips no aparecen

- **Solución**: Mantener presionado en lugar de tap rápido

---

## Mejores Prácticas

### Para Usuarios de Escritorio

1. Maximizar ventana del navegador
2. Usar zoom 100%
3. Aprovechar atajos de teclado (`Esc`, `Tab`)
4. Mantener múltiples pestañas abiertas para comparación

### Para Usuarios de Tablet

1. Usar modo horizontal
2. Cerrar sidebar cuando no se necesite
3. Aprovechar gestos táctiles (pinch, swipe)
4. Conectar teclado Bluetooth para mejor experiencia

### Para Usuarios de Móvil

1. **Usar solo para consultas rápidas**
2. Rotar a horizontal siempre que sea posible
3. Usar WiFi en lugar de datos móviles
4. Considerar instalar como PWA (futuro)

---

## Resumen de Recomendaciones

### **Uso Recomendado**

- **Escritorio/Laptop** (1366×768 o superior)
- Chrome, Edge o Firefox actualizados
- Conexión estable de internet
- Mouse para interacciones precisas

### **Uso Aceptable**

- **Tablet** (768×1024 o superior)
- Modo horizontal
- Para consultas y análisis moderado

### **No Recomendado**

- **Móvil** para análisis profundo
- Navegadores antiguos
- Conexiones lentas (<1 Mbps)
- Pantallas <360px de ancho

---

## Soporte

Si experimentas problemas de compatibilidad:

- **Email**: evalenci@eafit.edu.co
- **Reportar**: Incluir navegador, versión, dispositivo y captura de pantalla

---

**Última Actualización**: Febrero 2026
**Versión del Documento**: 1.0
