/// \file CrystalScorer.cc
/// \brief Geantino Labs (IFPR), nov/2026 — ver CrystalScorer.hh

#include "CrystalScorer.hh"

#include "G4Step.hh"
#include "G4VTouchable.hh"

namespace Geantino
{

std::map<G4int, G4ThreeVector> CrystalScorer::fCentres;

G4int CrystalScorer::GetIndex(G4Step* step)
{
  const G4VTouchable* touch = step->GetPreStepPoint()->GetTouchable();
  // profundidade 0 = cristal (copia 0..31), 1 = anel (copia 0..8)
  G4int index = touch->GetReplicaNumber(1) * 100 + touch->GetReplicaNumber(0);
  if (fCentres.find(index) == fCentres.end()) {
    fCentres[index] = touch->GetTranslation(0);
  }
  return index;
}

bool CrystalScorer::CentreOf(G4int index, G4ThreeVector& centre)
{
  auto it = fCentres.find(index);
  if (it == fCentres.end()) return false;
  centre = it->second;
  return true;
}

}  // namespace Geantino
