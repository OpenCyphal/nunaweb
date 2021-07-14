/**
 * Centrally defined functions for interfacing with the
 * backend API.
 *
 * Simplifies access to backend API routes in the frontend.
 */
import { APIError } from '~/services/errors.js';

// Nuxt configured base API backend URL
const BASE_URL = process.env.apiURL;

export function createUploadFormData(nsRepos, targetLang, targetEndian, flags, docURL) {
  // Create a FormData object to add data to
  // since API takes multipart/form-data
  const formData = new FormData();
  for (const repo of nsRepos) {
    if (typeof repo === 'string') {
      // Add as an archive URL
      formData.append('archive_urls', repo);
    } else if (repo === null || repo === '') {
      // Do nothing
    } else {
      // Add as an archive .zip file
      if (repo.type !== 'application/zip') {
        throw new TypeError('Only zip files are supported.');
      }
      formData.append('archive_files', repo);
    }
  }

  formData.append('target_lang', targetLang);
  formData.append('target_endian', targetEndian);
  formData.append('doc_url', docURL);

  for (const flag of flags) {
    if (flag.value === true) {
      formData.append('flags', flag.flag);
    }
  }

  return formData;
}

export async function upload(formData) {
  // Upload the form data.
  const res = await fetch(`${BASE_URL}/upload`, {
    method: 'POST',
    body: formData
  });

  if (!res.ok) {
    throw new APIError('Request failed with code ' + res.status + '.', res.status);
  }

  return await res.json();
}

export async function getStatus(taskID) {
  const res = await fetch(`${BASE_URL}/status/${taskID}`);
  if (!res.ok) {
    throw new APIError('Request failed with code ' + res.status + '.', res.status);
  }
  return await res.json();
}

export async function cancel(taskID) {
  const res = await fetch(`${BASE_URL}/status/${taskID}/cancel`);
  if (!res.ok) {
    throw new APIError('Request failed with code ' + res.status + '.', res.status);
  }
  return true;
}
