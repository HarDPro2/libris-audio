# CHANGELOG — Libris Audio

---

## [feature/book-owner-permissions] — 2026-07-01

- **Qué cambió:** El usuario que subió un libro puede ahora editarlo (título y categoría) y eliminarlo del catálogo global permanentemente. Los demás usuarios solo ven las opciones de su biblioteca personal, sin acceso a modificar el original.
- **Archivos tocados:**
  - `backend/main.py` — endpoints `DELETE /api/books/{id}` y `PATCH /api/books/{id}` con verificación JWT de ownership
  - `src/types/book.ts` — campo `uploadedBy?: string`
  - `src/hooks/useBooks.ts` — mapeo `added_by → uploadedBy`; funciones `deleteGlobalBook()` y `updateGlobalBook()`
  - `src/context/PlayerContext.tsx` — `deleteGlobalBook` y `updateGlobalBookMeta` expuestos en contexto
  - `src/components/libris/EditBookModal.tsx` — (**nuevo**) modal para editar título y categoría
  - `src/components/libris/BookCard.tsx` — menú de opciones diferenciado por propietario
  - `src/pages/LibraryPage.tsx` — pasa `currentUserId` a `BookCard`
- **Verificado:** TypeScript compila sin errores (`tsc --noEmit` limpio). Merge a `main` + push exitoso.
- **No verificado:** Prueba manual end-to-end en producción (requiere ejecutar el SQL en Supabase primero — ver nota abajo).
- **Impacto en docs/UI/marketing:** `CONTEXTO_PERMANENTE.md` actualizado con la nueva funcionalidad y el ítem del roadmap marcado como completado.

> **⚠️ ACCIÓN MANUAL REQUERIDA:** El usuario debe ejecutar el SQL de RLS y CASCADE FK en el Editor SQL de Supabase antes de que la función de borrado opere correctamente:
> ```sql
> CREATE POLICY "Owner can update own book" ON global_books FOR UPDATE USING (auth.uid() = added_by);
> CREATE POLICY "Owner can delete own book" ON global_books FOR DELETE USING (auth.uid() = added_by);
> ALTER TABLE user_books DROP CONSTRAINT IF EXISTS user_books_global_book_id_fkey,
>   ADD CONSTRAINT user_books_global_book_id_fkey FOREIGN KEY (global_book_id) REFERENCES global_books(id) ON DELETE CASCADE;
> ```

---

## [fix/player-paragraph-skipping] — 2026-07-01

- **Qué cambió:** Eliminada la condición de carrera entre el manejador `onEnded` y el `useEffect` de sincronización de src en `PlayerContext.tsx`. Se introdujo `isTransitioningRef` como guardia que impide que el efecto de sincronización interfiera cuando `onEnded` ya está manejando la transición entre partes de audio. Esto resuelve el salto de párrafos completos reportado por usuarios.
- **Archivos tocados:** `src/context/PlayerContext.tsx`
- **Verificado:** Commit `a7b687b` en main. TypeScript limpio.
- **No verificado:** Prueba en dispositivos reales (Brave, Safari, Opera Android).
- **Impacto en docs/UI:** Ninguno.
